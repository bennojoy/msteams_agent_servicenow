"""
Azure VM Tools for Teams Agent Bot.

This module provides tools for creating, managing, and monitoring Azure virtual machines.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents import function_tool
from pydantic import BaseModel

# Azure SDK imports
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import AzureError

from config.settings import settings
from utils.logger import get_logger, log_function_call, log_function_result, log_error_with_context

logger = get_logger(__name__)


# ---------- Helper Functions ----------
def get_azure_credential():
    """Get Azure credential based on configuration."""
    if settings.azure.client_id and settings.azure.client_secret and settings.azure.tenant_id:
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(
            tenant_id=settings.azure.tenant_id,
            client_id=settings.azure.client_id,
            client_secret=settings.azure.client_secret
        )
        logger.info("Using service principal authentication")
        return credential
    else:
        credential = DefaultAzureCredential()
        logger.info("Using DefaultAzureCredential (Azure CLI, Managed Identity, etc.)")
        return credential


# ---------- Data Models ----------
class VMCreateRequest(BaseModel):
    """Request model for VM creation."""
    name: str
    size: Optional[str] = None
    location: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    image_publisher: str = "Canonical"
    image_offer: str = "UbuntuServer"
    image_sku: str = "18.04-LTS"
    image_version: str = "latest"


class VMInfo(BaseModel):
    """VM information model."""
    name: str
    id: str
    location: str
    size: str
    power_state: str
    provisioning_state: str
    admin_username: str
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None
    created_time: Optional[str] = None


# ---------- Azure VM Tools ----------
@function_tool
async def create_vm(
    name: str,
    admin_username: str,
    admin_password: str,
    size: str,
    location: Optional[str] = None,
    image_publisher: str = "Canonical",
    image_offer: str = "UbuntuServer",
    image_sku: str = "18.04-LTS",
    image_version: str = "latest"
) -> Dict[str, Any]:
    """
    Create a new Azure virtual machine (without public IP).
    
    Args:
        name: Name of the VM
        admin_username: Admin username for the VM (required)
        admin_password: Admin password for the VM (required)
        size: VM size (required, e.g., Standard_B1s, Standard_D2s_v3, Standard_D4s_v3)
        location: Azure region (e.g., eastus, westus2)
        image_publisher: Image publisher
        image_offer: Image offer
        image_sku: Image SKU
        image_version: Image version
        
    Returns:
        Dictionary with VM creation result
        
    Note:
        VMs are created without public IP addresses for security. Use Azure Bastion,
        VPN, or internal network access to connect to the VMs.
    """
    log_function_call(logger, "create_vm", 
                     vm_name=name, size=size, location=location)
    
    try:
        # Use provided values or defaults from settings
        vm_size = size  # Use the provided size
        vm_location = location or settings.azure.location
        vm_admin_username = admin_username  # Use the provided username
        resource_group = settings.azure.resource_group
        
        # Initialize Azure clients
        credential = get_azure_credential()
        compute_client = ComputeManagementClient(credential, settings.azure.subscription_id)
        network_client = NetworkManagementClient(credential, settings.azure.subscription_id)
        resource_client = ResourceManagementClient(credential, settings.azure.subscription_id)
        
        # Create resource group if it doesn't exist
        logger.info(f"Creating/updating resource group: {resource_group}")
        resource_client.resource_groups.create_or_update(
            resource_group,
            {"location": vm_location}
        )
        
        # Create virtual network
        vnet_name = f"{name}-vnet"
        logger.info(f"Creating virtual network: {vnet_name}")
        vnet_params = {
            "location": vm_location,
            "address_space": {"address_prefixes": ["10.0.0.0/16"]},
            "subnets": [{
                "name": "default",
                "address_prefix": "10.0.0.0/24"
            }]
        }
        vnet_poller = network_client.virtual_networks.begin_create_or_update(
            resource_group, vnet_name, vnet_params
        )
        vnet = vnet_poller.result()
        
        # Create network interface (without public IP)
        nic_name = f"{name}-nic"
        logger.info(f"Creating network interface: {nic_name}")
        nic_params = {
            "location": vm_location,
            "ip_configurations": [{
                "name": "ipconfig1",
                "subnet": {"id": vnet.subnets[0].id}
            }]
        }
        nic_poller = network_client.network_interfaces.begin_create_or_update(
            resource_group, nic_name, nic_params
        )
        nic = nic_poller.result()
        
        # Create VM
        logger.info(f"Creating virtual machine: {name}")
        vm_params = {
            "location": vm_location,
            "hardware_profile": {"vm_size": vm_size},
            "storage_profile": {
                "image_reference": {
                    "publisher": image_publisher,
                    "offer": image_offer,
                    "sku": image_sku,
                    "version": image_version
                }
            },
            "network_profile": {
                "network_interfaces": [{"id": nic.id}]
            },
            "os_profile": {
                "computer_name": name,
                "admin_username": vm_admin_username,
                "admin_password": admin_password
            }
        }
        
        vm_poller = compute_client.virtual_machines.begin_create_or_update(
            resource_group, name, vm_params
        )
        vm = vm_poller.result()
        
        # Create VM info (without public IP)
        vm_info = VMInfo(
            name=vm.name,
            id=vm.id,
            location=vm.location,
            size=vm.hardware_profile.vm_size,
            power_state="VM running",
            provisioning_state=vm.provisioning_state,
            admin_username=vm_admin_username,
            public_ip=None,
            private_ip=nic.ip_configurations[0].private_ip_address,
            created_time=datetime.utcnow().isoformat()
        )
        
        result = {
            "success": True,
            "message": f"Virtual machine '{name}' created successfully (no public IP assigned)",
            "vm": vm_info.model_dump(),
            "connection_info": {
                "note": "VM created without public IP. Use Azure Bastion, VPN, or internal network access to connect.",
                "private_ip": nic.ip_configurations[0].private_ip_address
            }
        }
        
        log_function_result(logger, "create_vm", result, vm_name=name)
        return result
        
    except AzureError as e:
        log_error_with_context(logger, e, {
            "operation": "create_vm",
            "vm_name": name,
            "size": size,
            "location": location
        })
        
        return {
            "success": False,
            "error": f"Azure error creating VM '{name}': {str(e)}"
        }
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "create_vm",
            "vm_name": name,
            "size": size,
            "location": location
        })
        
        return {
            "success": False,
            "error": f"Failed to create VM '{name}': {str(e)}"
        }


@function_tool
async def list_vms() -> Dict[str, Any]:
    """
    List all virtual machines in the resource group.
    
    Returns:
        Dictionary with list of VMs
    """
    log_function_call(logger, "list_vms")
    
    try:
        # Initialize Azure clients
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, settings.azure.subscription_id)
        network_client = NetworkManagementClient(credential, settings.azure.subscription_id)
        
        resource_group = settings.azure.resource_group
        
        # List all VMs in the resource group
        vm_list = compute_client.virtual_machines.list(resource_group)
        vms = []
        
        for vm in vm_list:
            # Get VM instance view to get power state
            vm_instance = compute_client.virtual_machines.instance_view(resource_group, vm.name)
            power_state = "Unknown"
            for status in vm_instance.statuses:
                if status.code.startswith("PowerState/"):
                    power_state = status.code.replace("PowerState/", "")
                    break
            
            # Get network interface to get IP addresses
            public_ip = None
            private_ip = None
            if vm.network_profile and vm.network_profile.network_interfaces:
                nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
                try:
                    nic = network_client.network_interfaces.get(resource_group, nic_name)
                    if nic.ip_configurations:
                        private_ip = nic.ip_configurations[0].private_ip_address
                        if nic.ip_configurations[0].public_ip_address:
                            pip_name = nic.ip_configurations[0].public_ip_address.id.split('/')[-1]
                            pip = network_client.public_ip_addresses.get(resource_group, pip_name)
                            public_ip = pip.ip_address
                except Exception as e:
                    logger.warning(f"Could not get network info for VM {vm.name}: {e}")
            
            vm_info = VMInfo(
                name=vm.name,
                id=vm.id,
                location=vm.location,
                size=vm.hardware_profile.vm_size,
                power_state=power_state,
                provisioning_state=vm.provisioning_state,
                admin_username=vm.os_profile.admin_username if vm.os_profile else "Unknown",
                public_ip=public_ip,
                private_ip=private_ip,
                created_time=vm.tags.get("created_time") if vm.tags else None
            )
            vms.append(vm_info)
        
        result = {
            "success": True,
            "count": len(vms),
            "vms": [vm.model_dump() for vm in vms]
        }
        
        log_function_result(logger, "list_vms", result, vm_count=len(vms))
        return result
        
    except AzureError as e:
        log_error_with_context(logger, e, {"operation": "list_vms"})
        return {
            "success": False,
            "error": f"Azure error listing VMs: {str(e)}"
        }
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "list_vms"})
        return {
            "success": False,
            "error": f"Failed to list VMs: {str(e)}"
        }


@function_tool
async def get_vm_status(vm_name: str) -> Dict[str, Any]:
    """
    Get the status of a specific virtual machine.
    
    Args:
        vm_name: Name of the VM
        
    Returns:
        Dictionary with VM status
    """
    log_function_call(logger, "get_vm_status", vm_name=vm_name)
    
    try:
        # Initialize Azure clients
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, settings.azure.subscription_id)
        network_client = NetworkManagementClient(credential, settings.azure.subscription_id)
        
        resource_group = settings.azure.resource_group
        
        # Get VM details
        vm = compute_client.virtual_machines.get(resource_group, vm_name)
        
        # Get VM instance view to get power state
        vm_instance = compute_client.virtual_machines.instance_view(resource_group, vm_name)
        power_state = "Unknown"
        for status in vm_instance.statuses:
            if status.code.startswith("PowerState/"):
                power_state = status.code.replace("PowerState/", "")
                break
        
        # Get network interface to get IP addresses
        public_ip = None
        private_ip = None
        if vm.network_profile and vm.network_profile.network_interfaces:
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            try:
                nic = network_client.network_interfaces.get(resource_group, nic_name)
                if nic.ip_configurations:
                    private_ip = nic.ip_configurations[0].private_ip_address
                    if nic.ip_configurations[0].public_ip_address:
                        pip_name = nic.ip_configurations[0].public_ip_address.id.split('/')[-1]
                        pip = network_client.public_ip_addresses.get(resource_group, pip_name)
                        public_ip = pip.ip_address
            except Exception as e:
                logger.warning(f"Could not get network info for VM {vm_name}: {e}")
        
        vm_info = VMInfo(
            name=vm.name,
            id=vm.id,
            location=vm.location,
            size=vm.hardware_profile.vm_size,
            power_state=power_state,
            provisioning_state=vm.provisioning_state,
            admin_username=vm.os_profile.admin_username if vm.os_profile else "Unknown",
            public_ip=public_ip,
            private_ip=private_ip,
            created_time=vm.tags.get("created_time") if vm.tags else None
        )
        
        result = {
            "success": True,
            "vm": vm_info.model_dump(),
            "status_summary": f"VM '{vm_name}' is {vm_info.power_state.lower()} in {vm_info.location}"
        }
        
        log_function_result(logger, "get_vm_status", result, vm_name=vm_name)
        return result
        
    except AzureError as e:
        log_error_with_context(logger, e, {
            "operation": "get_vm_status",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Azure error getting status for VM '{vm_name}': {str(e)}"
        }
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "get_vm_status",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Failed to get status for VM '{vm_name}': {str(e)}"
        }


@function_tool
async def start_vm(vm_name: str) -> Dict[str, Any]:
    """
    Start a virtual machine.
    
    Args:
        vm_name: Name of the VM to start
        
    Returns:
        Dictionary with operation result
    """
    log_function_call(logger, "start_vm", vm_name=vm_name)
    
    try:
        # Initialize Azure client
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, settings.azure.subscription_id)
        
        resource_group = settings.azure.resource_group
        
        # Start the VM
        logger.info(f"Starting VM: {vm_name}")
        start_poller = compute_client.virtual_machines.begin_start(resource_group, vm_name)
        start_poller.result()  # Wait for the operation to complete
        
        result = {
            "success": True,
            "message": f"Virtual machine '{vm_name}' started successfully",
            "vm_name": vm_name,
            "operation": "start"
        }
        
        log_function_result(logger, "start_vm", result, vm_name=vm_name)
        return result
        
    except AzureError as e:
        log_error_with_context(logger, e, {
            "operation": "start_vm",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Azure error starting VM '{vm_name}': {str(e)}"
        }
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "start_vm",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Failed to start VM '{vm_name}': {str(e)}"
        }


@function_tool
async def stop_vm(vm_name: str) -> Dict[str, Any]:
    """
    Stop a virtual machine.
    
    Args:
        vm_name: Name of the VM to stop
        
    Returns:
        Dictionary with operation result
    """
    log_function_call(logger, "stop_vm", vm_name=vm_name)
    
    try:
        # Initialize Azure client
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, settings.azure.subscription_id)
        
        resource_group = settings.azure.resource_group
        
        # Stop the VM
        logger.info(f"Stopping VM: {vm_name}")
        stop_poller = compute_client.virtual_machines.begin_deallocate(resource_group, vm_name)
        stop_poller.result()  # Wait for the operation to complete
        
        result = {
            "success": True,
            "message": f"Virtual machine '{vm_name}' stopped successfully",
            "vm_name": vm_name,
            "operation": "stop"
        }
        
        log_function_result(logger, "stop_vm", result, vm_name=vm_name)
        return result
        
    except AzureError as e:
        log_error_with_context(logger, e, {
            "operation": "stop_vm",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Azure error stopping VM '{vm_name}': {str(e)}"
        }
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "stop_vm",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Failed to stop VM '{vm_name}': {str(e)}"
        }


@function_tool
async def delete_vm(vm_name: str, confirm: bool = False) -> Dict[str, Any]:
    """
    Delete a virtual machine.
    
    Args:
        vm_name: Name of the VM to delete
        confirm: Must be True to confirm deletion
        
    Returns:
        Dictionary with operation result
    """
    log_function_call(logger, "delete_vm", vm_name=vm_name, confirm=confirm)
    
    if not confirm:
        return {
            "success": False,
            "error": "Deletion not confirmed. Set confirm=True to proceed.",
            "warning": "This operation will permanently delete the VM and its associated resources."
        }
    
    try:
        # Initialize Azure clients
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, settings.azure.subscription_id)
        network_client = NetworkManagementClient(credential, settings.azure.subscription_id)
        
        resource_group = settings.azure.resource_group
        
        # Get VM details to find associated resources
        vm = compute_client.virtual_machines.get(resource_group, vm_name)
        
        # Delete the VM
        logger.info(f"Deleting VM: {vm_name}")
        delete_poller = compute_client.virtual_machines.begin_delete(resource_group, vm_name)
        delete_poller.result()  # Wait for the operation to complete
        
        # Delete associated network resources
        if vm.network_profile and vm.network_profile.network_interfaces:
            for nic_ref in vm.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                logger.info(f"Deleting network interface: {nic_name}")
                
                # Get NIC details to find public IP (if any)
                try:
                    nic = network_client.network_interfaces.get(resource_group, nic_name)
                    if nic.ip_configurations and nic.ip_configurations[0].public_ip_address:
                        pip_name = nic.ip_configurations[0].public_ip_address.id.split('/')[-1]
                        logger.info(f"Deleting public IP: {pip_name}")
                        network_client.public_ip_addresses.begin_delete(resource_group, pip_name).result()
                    else:
                        logger.info(f"No public IP found for NIC: {nic_name}")
                except Exception as e:
                    logger.warning(f"Could not delete associated network resources: {e}")
                
                # Delete the NIC
                network_client.network_interfaces.begin_delete(resource_group, nic_name).result()
        
        result = {
            "success": True,
            "message": f"Virtual machine '{vm_name}' and associated resources deleted successfully",
            "vm_name": vm_name,
            "operation": "delete"
        }
        
        log_function_result(logger, "delete_vm", result, vm_name=vm_name)
        return result
        
    except AzureError as e:
        log_error_with_context(logger, e, {
            "operation": "delete_vm",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Azure error deleting VM '{vm_name}': {str(e)}"
        }
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "delete_vm",
            "vm_name": vm_name
        })
        return {
            "success": False,
            "error": f"Failed to delete VM '{vm_name}': {str(e)}"
        }


# ---------- Tool Registration ----------
def get_azure_vm_tools() -> List:
    """Get all Azure VM tools for registration with agents."""
    return [
        create_vm,
        list_vms,
        get_vm_status,
        start_vm,
        stop_vm,
        delete_vm
    ] 