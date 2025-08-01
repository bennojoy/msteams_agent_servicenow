"""
ServiceNow Catalog Creation Tools for Teams Agent Bot.

This module provides tools for creating ServiceNow catalog items only.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from agents import function_tool
from utils.logger import get_logger, log_function_call, log_function_result, log_error_with_context
from openai_agents.servicenow_api import get_servicenow_client

logger = get_logger(__name__)


# ---------- ServiceNow Tools ----------
@function_tool
async def create_catalog_item(
    name: str,
    short_description: str,
    long_description: str,
    category: str,
    catalog_type: str = "item"
) -> Dict[str, Any]:
    """
    Create a new catalog item in ServiceNow (without variables).
    
    This function creates a new catalog item with the specified details.
    Variables can be added separately using the ServiceNow Variables Agent.
    
    Args:
        name: Catalog item name
        short_description: Short description for the catalog item
        long_description: Long description for the catalog item
        category: Category name
        catalog_type: Type of catalog (default: "item")
        
    Returns:
        Dict containing the creation result and catalog item details
    """
    log_function_call(logger, "create_catalog_item", 
                     name=name, category=category, catalog_type=catalog_type)
    
    try:
        # Get ServiceNow client
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        # Log the tool call details
        logger.info({
            "event": "catalog_creation_tool_call",
            "tool": "create_catalog_item",
            "parameters": {
                "name": name,
                "short_description": short_description,
                "long_description": long_description,
                "category": category,
                "catalog_type": catalog_type
            }
        })
        
        # Create the catalog item
        result = servicenow.create_catalog_item(
            name=name,
            short_description=short_description,
            long_description=long_description,
            category=category,
            catalog_type=catalog_type
        )
        
        log_function_result(logger, "create_catalog_item", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "create_catalog_item",
            "name": name,
            "category": category
        })
        return {
            "success": False,
            "error": f"Failed to create catalog item: {str(e)}"
        }


@function_tool
async def create_and_publish_catalog_item(
    name: str,
    short_description: str,
    long_description: str,
    category: str,
    catalog_type: str = "item"
) -> Dict[str, Any]:
    """
    Create and publish a new catalog item in ServiceNow (without variables).
    
    This function creates a new catalog item and automatically publishes it to make it visible.
    Variables can be added separately using the ServiceNow Variables Agent.
    
    Args:
        name: Catalog item name
        short_description: Short description for the catalog item
        long_description: Long description for the catalog item
        category: Category name
        catalog_type: Type of catalog (default: "item")
        
    Returns:
        Dict containing the creation and publishing result and catalog item details
    """
    log_function_call(logger, "create_and_publish_catalog_item", 
                     name=name, category=category, catalog_type=catalog_type)
    
    try:
        # Get ServiceNow client
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        # Log the tool call details
        logger.info({
            "event": "catalog_creation_tool_call",
            "tool": "create_and_publish_catalog_item",
            "parameters": {
                "name": name,
                "short_description": short_description,
                "long_description": long_description,
                "category": category,
                "catalog_type": catalog_type
            }
        })
        
        # Create the catalog item
        create_result = servicenow.create_catalog_item(
            name=name,
            short_description=short_description,
            long_description=long_description,
            category=category,
            catalog_type=catalog_type
        )
        
        if not create_result.get('success'):
            return create_result
        
        # Get the catalog ID from the creation result
        catalog_id = create_result.get('catalog_id')
        if not catalog_id:
            return {
                "success": False,
                "error": "Failed to get catalog ID from creation result"
            }
        
        # Publish the catalog item
        publish_result = servicenow.publish_catalog_item(catalog_id)
        
        if publish_result.get('success'):
            # Combine the results with enhanced details
            result = {
                "success": True,
                "catalog_id": catalog_id,
                "catalog_name": name,
                "message": f"✅ Catalog item '{name}' created and published successfully!",
                "details": {
                    "name": name,
                    "sys_id": catalog_id,
                    "number": create_result.get('details', {}).get('number', ''),
                    "status": "active",
                    "published": True,
                    "short_description": short_description,
                    "long_description": long_description,
                    "category": category,
                    "catalog_type": catalog_type
                },
                "summary": f"""
🎉 **CATALOG ITEM CREATED SUCCESSFULLY**

📋 **Item Details:**
• **Name:** {name}
• **Catalog ID:** {catalog_id}
• **Catalog Number:** {create_result.get('details', {}).get('number', 'N/A')}
• **Category:** {category}
• **Type:** {catalog_type}
• **Status:** Active & Published

📝 **Descriptions:**
• **Short:** {short_description}
• **Long:** {long_description}

✅ The catalog item is now live and available for users to request!
"""
            }
        else:
            # Creation succeeded but publishing failed
            result = {
                "success": False,
                "catalog_id": catalog_id,
                "catalog_name": name,
                "message": f"⚠️ Catalog item '{name}' created but failed to publish",
                "error": publish_result.get('error', 'Unknown publishing error'),
                "details": create_result.get('details', {}),
                "summary": f"""
⚠️ **CATALOG ITEM CREATED BUT PUBLISHING FAILED**

📋 **Item Details:**
• **Name:** {name}
• **Catalog ID:** {catalog_id}
• **Status:** Created (not published)

❌ **Publishing Error:** {publish_result.get('error', 'Unknown error')}

The catalog item was created but is not yet visible to users. You may need to publish it manually.
"""
            }
        
        log_function_result(logger, "create_and_publish_catalog_item", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "create_and_publish_catalog_item",
            "name": name,
            "category": category
        })
        return {
            "success": False,
            "error": f"Failed to create and publish catalog item: {str(e)}"
        }


@function_tool
async def publish_catalog_item(catalog_identifier: str) -> Dict[str, Any]:
    """
    Publish a catalog item to make it visible in the Service Catalog.
    
    Args:
        catalog_identifier: Catalog ID or name
        
    Returns:
        Dict containing the publishing result
    """
    log_function_call(logger, "publish_catalog_item", catalog_identifier=catalog_identifier)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.publish_catalog_item(catalog_identifier)
        
        log_function_result(logger, "publish_catalog_item", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "publish_catalog_item",
            "catalog_identifier": catalog_identifier
        })
        return {
            "success": False,
            "error": f"Failed to publish catalog item: {str(e)}"
        }


@function_tool
async def get_servicenow_categories() -> Dict[str, Any]:
    """
    Get available ServiceNow categories.
    
    Returns:
        Dict containing available categories from ServiceNow
    """
    log_function_call(logger, "get_servicenow_categories")
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.get_available_categories()
        
        log_function_result(logger, "get_servicenow_categories", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "get_servicenow_categories"})
        return {
            "success": False,
            "error": f"Failed to get categories: {str(e)}"
        }


@function_tool
async def get_servicenow_catalog_types() -> Dict[str, Any]:
    """
    Get available ServiceNow catalog types.
    
    Returns:
        Dict containing available catalog types from ServiceNow
    """
    log_function_call(logger, "get_servicenow_catalog_types")
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.get_available_catalog_types()
        
        log_function_result(logger, "get_servicenow_catalog_types", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "get_servicenow_catalog_types"})
        return {
            "success": False,
            "error": f"Failed to get catalog types: {str(e)}"
        }


@function_tool
async def link_variable_set_to_catalog(
    catalog_identifier: str,
    variable_set_id: str
) -> Dict[str, Any]:
    """
    Link a variable set to a catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name
        variable_set_id: Variable set sys_id to link
        
    Returns:
        Dict containing the linking result
    """
    log_function_call(logger, "link_variable_set_to_catalog", 
                     catalog_identifier=catalog_identifier,
                     variable_set_id=variable_set_id)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.link_variable_set_to_catalog(
            catalog_identifier=catalog_identifier,
            variable_set_id=variable_set_id
        )
        
        log_function_result(logger, "link_variable_set_to_catalog", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "link_variable_set_to_catalog",
            "catalog_identifier": catalog_identifier,
            "variable_set_id": variable_set_id
        })
        return {
            "success": False,
            "error": f"Failed to link variable set: {str(e)}"
        }


def get_servicenow_catalog_tools():
    """Get ServiceNow catalog creation tools for the agent."""
    return [
        create_catalog_item,
        create_and_publish_catalog_item,
        publish_catalog_item,
        get_servicenow_categories,
        get_servicenow_catalog_types,
        link_variable_set_to_catalog
    ] 