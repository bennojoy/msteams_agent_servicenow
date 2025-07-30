"""
ServiceNow Tools for Teams Agent Bot.

This module provides tools for interacting with ServiceNow, specifically for
catalog item creation and management using modular functions.
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


# ---------- Data Models ----------
class ServiceNowVariable(TypedDict, total=False):
    """Model for ServiceNow catalog item variables."""
    name: str
    label: str
    type: str
    default_value: Optional[str]
    required: bool
    help_text: Optional[str]
    choices: Optional[List[str]]


class ServiceNowCatalogItem(TypedDict, total=False):
    """Model for ServiceNow catalog item creation."""
    name: str
    catalog_type: str
    category: str
    short_description: str
    long_description: str
    variables: Optional[List[ServiceNowVariable]]


# ---------- ServiceNow Configuration ----------
SERVICENOW_VARIABLE_TYPES = [
    "string", "boolean", "multiple_choice", "date"
]

SERVICENOW_CATALOG_TYPES = ["service", "hardware", "employee"]
SERVICENOW_CATEGORIES = ["incident", "inventory"]


# ---------- ServiceNow Tools ----------
@function_tool
async def create_catalog_item(
    name: str,
    description: str,
    category: str,
    catalog_type: str = "item"
) -> Dict[str, Any]:
    """
    Create a new catalog item in ServiceNow (without variables).
    
    This function creates a new catalog item with the specified details.
    Variables can be added separately using the add_variable functions.
    
    Args:
        name: Catalog item name
        description: Description for the catalog item
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
        
        # Create the catalog item
        result = servicenow.create_catalog_item(
            name=name,
            description=description,
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
async def add_string_variable(
    catalog_identifier: str,
    name: str,
    label: str,
    required: bool = False,
    default_value: Optional[str] = None,
    help_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a string variable to a catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name
        name: Variable name
        label: Display label
        required: Whether the variable is required
        default_value: Default value (optional)
        help_text: Help text (optional)
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_string_variable", 
                     catalog_identifier=catalog_identifier, name=name, label=label)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.create_string_variable(
            catalog_identifier=catalog_identifier,
            name=name,
            label=label,
            required=required,
            default_value=default_value,
            help_text=help_text
        )
        
        log_function_result(logger, "add_string_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_string_variable",
            "catalog_identifier": catalog_identifier,
            "name": name
        })
        return {
            "success": False,
            "error": f"Failed to add string variable: {str(e)}"
        }


@function_tool
async def add_boolean_variable(
    catalog_identifier: str,
    name: str,
    label: str,
    required: bool = False,
    default_value: bool = False,
    help_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a boolean variable to a catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name
        name: Variable name
        label: Display label
        required: Whether the variable is required
        default_value: Default value (true/false)
        help_text: Help text (optional)
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_boolean_variable", 
                     catalog_identifier=catalog_identifier, name=name, label=label)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.create_boolean_variable(
            catalog_identifier=catalog_identifier,
            name=name,
            label=label,
            required=required,
            default_value=default_value,
            help_text=help_text
        )
        
        log_function_result(logger, "add_boolean_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_boolean_variable",
            "catalog_identifier": catalog_identifier,
            "name": name
        })
        return {
            "success": False,
            "error": f"Failed to add boolean variable: {str(e)}"
        }


@function_tool
async def add_multiple_choice_variable(
    catalog_identifier: str,
    name: str,
    label: str,
    choices: List[str],
    required: bool = False,
    default_value: Optional[str] = None,
    help_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a multiple choice variable (radio buttons) to a catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name
        name: Variable name
        label: Display label
        choices: List of choice options
        required: Whether the variable is required
        default_value: Default value (optional)
        help_text: Help text (optional)
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_multiple_choice_variable", 
                     catalog_identifier=catalog_identifier, name=name, label=label, choices=choices)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.create_multiple_choice_variable(
            catalog_identifier=catalog_identifier,
            name=name,
            label=label,
            choices=choices,
            required=required,
            default_value=default_value,
            help_text=help_text
        )
        
        log_function_result(logger, "add_multiple_choice_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_multiple_choice_variable",
            "catalog_identifier": catalog_identifier,
            "name": name
        })
        return {
            "success": False,
            "error": f"Failed to add multiple choice variable: {str(e)}"
        }


@function_tool
async def add_date_variable(
    catalog_identifier: str,
    name: str,
    label: str,
    required: bool = False,
    default_value: Optional[str] = None,
    help_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a date variable to a catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name
        name: Variable name
        label: Display label
        required: Whether the variable is required
        default_value: Default value (optional, date format)
        help_text: Help text (optional)
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_date_variable", 
                     catalog_identifier=catalog_identifier, name=name, label=label)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.create_date_variable(
            catalog_identifier=catalog_identifier,
            name=name,
            label=label,
            required=required,
            default_value=default_value,
            help_text=help_text
        )
        
        log_function_result(logger, "add_date_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_date_variable",
            "catalog_identifier": catalog_identifier,
            "name": name
        })
        return {
            "success": False,
            "error": f"Failed to add date variable: {str(e)}"
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
async def get_servicenow_variable_types() -> Dict[str, Any]:
    """
    Get available ServiceNow variable types.
    
    Returns:
        Dict containing available variable types
    """
    log_function_call(logger, "get_servicenow_variable_types")
    
    try:
        return {
            "success": True,
            "variable_types": SERVICENOW_VARIABLE_TYPES,
            "count": len(SERVICENOW_VARIABLE_TYPES),
            "descriptions": {
                "string": "Single line text input",
                "boolean": "Checkbox (true/false)",
                "multiple_choice": "Radio button group",
                "date": "Date picker"
            }
        }
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "get_servicenow_variable_types"})
        return {
            "success": False,
            "error": f"Failed to get variable types: {str(e)}"
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


def get_servicenow_tools():
    """Get all ServiceNow tools for the agent."""
    return [
        create_catalog_item,
        add_string_variable,
        add_boolean_variable,
        add_multiple_choice_variable,
        add_date_variable,
        publish_catalog_item,
        get_servicenow_variable_types,
        get_servicenow_categories,
        get_servicenow_catalog_types
    ] 