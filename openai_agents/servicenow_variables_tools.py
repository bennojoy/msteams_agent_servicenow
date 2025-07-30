"""
ServiceNow Variables Tools for Teams Agent Bot.

This module provides tools for adding variables to existing ServiceNow catalog items.
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


# ---------- ServiceNow Catalog Lookup Tools ----------
@function_tool
async def search_catalog_items(search_term: str = None, limit: int = 10) -> Dict[str, Any]:
    """
    Search for catalog items by name or description.
    
    Args:
        search_term: Optional search term to filter results
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        Dict containing matching catalog items
    """
    log_function_call(logger, "search_catalog_items", search_term=search_term, limit=limit)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.search_catalog_items(search_term=search_term, limit=limit)
        
        log_function_result(logger, "search_catalog_items", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "search_catalog_items",
            "search_term": search_term
        })
        return {
            "success": False,
            "error": f"Failed to search catalog items: {str(e)}"
        }


@function_tool
async def list_catalog_items(category: str = None, limit: int = 20) -> Dict[str, Any]:
    """
    List catalog items, optionally filtered by category.
    
    Args:
        category: Optional category to filter by
        limit: Maximum number of results to return (default: 20)
        
    Returns:
        Dict containing catalog items list
    """
    log_function_call(logger, "list_catalog_items", category=category, limit=limit)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.list_catalog_items(category=category, limit=limit)
        
        log_function_result(logger, "list_catalog_items", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "list_catalog_items",
            "category": category
        })
        return {
            "success": False,
            "error": f"Failed to list catalog items: {str(e)}"
        }


@function_tool
async def get_catalog_details(catalog_identifier: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific catalog item.
    
    Args:
        catalog_identifier: Catalog ID, name, or number
        
    Returns:
        Dict containing catalog item details
    """
    log_function_call(logger, "get_catalog_details", catalog_identifier=catalog_identifier)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.get_catalog_item(catalog_identifier)
        
        log_function_result(logger, "get_catalog_details", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "get_catalog_details",
            "catalog_identifier": catalog_identifier
        })
        return {
            "success": False,
            "error": f"Failed to get catalog details: {str(e)}"
        }


# ---------- ServiceNow Variable Tools ----------
@function_tool
async def add_string_variable(
    catalog_identifier: str,
    variable_name: str,
    question_text: str,
    default_value: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a string variable to an existing ServiceNow catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name (smart detection)
        variable_name: Name of the variable
        question_text: Display text for the variable
        default_value: Optional default value
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_string_variable", 
                     catalog_identifier=catalog_identifier, variable_name=variable_name)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        # Log the tool call details
        logger.info({
            "event": "variable_creation_tool_call",
            "tool": "add_string_variable",
            "parameters": {
                "catalog_identifier": catalog_identifier,
                "variable_name": variable_name,
                "question_text": question_text,
                "default_value": default_value
            }
        })
        
        result = servicenow.add_string_variable(
            catalog_identifier=catalog_identifier,
            variable_name=variable_name,
            question_text=question_text,
            default_value=default_value
        )
        
        log_function_result(logger, "add_string_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_string_variable",
            "catalog_identifier": catalog_identifier,
            "variable_name": variable_name
        })
        return {
            "success": False,
            "error": f"Failed to add string variable: {str(e)}"
        }


@function_tool
async def add_boolean_variable(
    catalog_identifier: str,
    variable_name: str,
    question_text: str,
    default_value: bool = False
) -> Dict[str, Any]:
    """
    Add a boolean variable to an existing ServiceNow catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name (smart detection)
        variable_name: Name of the variable
        question_text: Display text for the variable
        default_value: Default boolean value (default: False)
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_boolean_variable", 
                     catalog_identifier=catalog_identifier, variable_name=variable_name)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.add_boolean_variable(
            catalog_identifier=catalog_identifier,
            variable_name=variable_name,
            question_text=question_text,
            default_value=default_value
        )
        
        log_function_result(logger, "add_boolean_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_boolean_variable",
            "catalog_identifier": catalog_identifier,
            "variable_name": variable_name
        })
        return {
            "success": False,
            "error": f"Failed to add boolean variable: {str(e)}"
        }


@function_tool
async def add_multiple_choice_variable(
    catalog_identifier: str,
    variable_name: str,
    question_text: str,
    choices: List[str],
    default_value: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a multiple choice variable to an existing ServiceNow catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name (smart detection)
        variable_name: Name of the variable
        question_text: Display text for the variable
        choices: List of choice options
        default_value: Optional default choice
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_multiple_choice_variable", 
                     catalog_identifier=catalog_identifier, variable_name=variable_name)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.add_multiple_choice_variable(
            catalog_identifier=catalog_identifier,
            variable_name=variable_name,
            question_text=question_text,
            choices=choices,
            default_value=default_value
        )
        
        log_function_result(logger, "add_multiple_choice_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_multiple_choice_variable",
            "catalog_identifier": catalog_identifier,
            "variable_name": variable_name
        })
        return {
            "success": False,
            "error": f"Failed to add multiple choice variable: {str(e)}"
        }


@function_tool
async def add_date_variable(
    catalog_identifier: str,
    variable_name: str,
    question_text: str,
    default_value: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a date variable to an existing ServiceNow catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name (smart detection)
        variable_name: Name of the variable
        question_text: Display text for the variable
        default_value: Optional default date (YYYY-MM-DD format)
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_date_variable", 
                     catalog_identifier=catalog_identifier, variable_name=variable_name)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.add_date_variable(
            catalog_identifier=catalog_identifier,
            variable_name=variable_name,
            question_text=question_text,
            default_value=default_value
        )
        
        log_function_result(logger, "add_date_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_date_variable",
            "catalog_identifier": catalog_identifier,
            "variable_name": variable_name
        })
        return {
            "success": False,
            "error": f"Failed to add date variable: {str(e)}"
        }


@function_tool
async def add_select_box_variable(
    catalog_identifier: str,
    variable_name: str,
    question_text: str,
    choices: List[str],
    default_value: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a select box (dropdown) variable to an existing ServiceNow catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name (smart detection)
        variable_name: Name of the variable
        question_text: Display text for the variable
        choices: List of choice options
        default_value: Optional default choice
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_select_box_variable", 
                     catalog_identifier=catalog_identifier, variable_name=variable_name)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.create_choice_variable(
            catalog_identifier=catalog_identifier,
            name=variable_name,
            label=question_text,
            choices=choices,
            default_value=default_value
        )
        
        log_function_result(logger, "add_select_box_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_select_box_variable",
            "catalog_identifier": catalog_identifier,
            "variable_name": variable_name
        })
        return {
            "success": False,
            "error": f"Failed to add select box variable: {str(e)}"
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
    Get available ServiceNow variable types and their descriptions.
    
    Returns:
        Dict containing available variable types and their details
    """
    log_function_call(logger, "get_servicenow_variable_types")
    
    try:
        result = {
            "success": True,
            "variable_types": {
                "string": {
                    "description": "Single line text input",
                    "type_code": "6",
                    "display": "String/Single line text"
                },
                "boolean": {
                    "description": "True/False checkbox",
                    "type_code": "1", 
                    "display": "Boolean (Yes/No)"
                },
                "multiple_choice": {
                    "description": "Radio buttons with predefined choices",
                    "type_code": "3",
                    "display": "Multiple Choice"
                },
                "select_box": {
                    "description": "Dropdown with predefined choices",
                    "type_code": "5",
                    "display": "Select Box"
                },
                "date": {
                    "description": "Date picker",
                    "type_code": "9",
                    "display": "Date"
                }
            }
        }
        
        log_function_result(logger, "get_servicenow_variable_types", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "get_servicenow_variable_types"})
        return {
            "success": False,
            "error": f"Failed to get variable types: {str(e)}"
        }


def get_servicenow_variables_tools():
    """Get ServiceNow variables tools for the agent."""
    return [
        # Catalog lookup tools
        search_catalog_items,
        list_catalog_items,
        get_catalog_details,
        # Variable creation tools
        add_string_variable,
        add_boolean_variable,
        add_multiple_choice_variable,
        add_select_box_variable,
        add_date_variable,
        # Publishing tool
        publish_catalog_item,
        # Variable types tool
        get_servicenow_variable_types
    ] 