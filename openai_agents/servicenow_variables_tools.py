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

class VariableDefinition(BaseModel):
    """Pydantic model for variable definitions in batch creation."""
    type: str = Field(..., description="Variable type: 'string', 'boolean', 'choice', 'multiple_choice', 'date', 'reference'")
    name: str = Field(..., description="Variable name")
    label: str = Field(..., description="Question text/label that users will see")
    required: bool = Field(default=False, description="Whether variable is required")
    default_value: Optional[str] = Field(default=None, description="Default value for the variable")
    help_text: Optional[str] = Field(default=None, description="Help text for the variable")
    choices: Optional[List[str]] = Field(default=None, description="List of choices for choice/multiple_choice variables")
    reference_table: Optional[str] = Field(default=None, description="Reference table for reference variables")
    reference_qual_condition: Optional[str] = Field(default="active=true", description="Reference qualifier condition for reference variables")


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
async def add_reference_variable(
    catalog_identifier: str,
    variable_name: str,
    question_text: str,
    reference_table: str,
    reference_qual_condition: str = "active=true"
) -> Dict[str, Any]:
    """
    Add a Reference variable to a catalog item.
    
    Args:
        catalog_identifier: Catalog ID or name
        variable_name: Name of the variable
        question_text: Display text for the variable
        reference_table: ServiceNow table to reference (e.g., "sys_user", "cmn_location")
        reference_qual_condition: Filter condition for the reference table (default: "active=true")
        
    Returns:
        Dict containing the creation result
    """
    log_function_call(logger, "add_reference_variable", 
                     catalog_identifier=catalog_identifier,
                     variable_name=variable_name,
                     question_text=question_text,
                     reference_table=reference_table,
                     reference_qual_condition=reference_qual_condition)
    
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                "success": False,
                "error": "ServiceNow client not available"
            }
        
        result = servicenow.add_reference_variable(
            catalog_identifier=catalog_identifier,
            variable_name=variable_name,
            question_text=question_text,
            reference_table=reference_table,
            reference_qual_condition=reference_qual_condition
        )
        
        log_function_result(logger, "add_reference_variable", result)
        return result
        
    except Exception as e:
        log_error_with_context(logger, e, {
            "operation": "add_reference_variable",
            "catalog_identifier": catalog_identifier,
            "variable_name": variable_name,
            "reference_table": reference_table
        })
        return {
            "success": False,
            "error": f"Failed to add reference variable: {str(e)}"
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
                },
                "reference": {
                    "description": "Reference to another ServiceNow table",
                    "type_code": "8",
                    "display": "Reference"
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


@function_tool
async def add_multiple_variables(catalog_identifier: str, variables: List[VariableDefinition]) -> Dict[str, Any]:
    """
    Create multiple variables for a catalog item with proper order sequencing.
    
    Args:
        catalog_identifier: Catalog item ID or number
        variables: List of variable definitions with proper structure
    
    Returns:
        Dictionary with success status and results
    """
    try:
        servicenow = get_servicenow_client()
        if not servicenow:
            return {
                'success': False,
                'error': 'ServiceNow client not initialized'
            }
        
        logger.info({
            "event": "batch_variable_creation_tool_called",
            "catalog_identifier": catalog_identifier,
            "variable_count": len(variables)
        })
        
        # Convert Pydantic models to dictionaries for the API call
        variables_dict = [var.model_dump() for var in variables]
        result = servicenow.create_multiple_variables(catalog_identifier, variables_dict)
        
        logger.info({
            "event": "batch_variable_creation_tool_completed",
            "catalog_identifier": catalog_identifier,
            "total_created": result.get('total_created', 0),
            "total_failed": result.get('total_failed', 0),
            "success": result.get('success', False)
        })
        
        return result
        
    except Exception as e:
        logger.error({
            "event": "batch_variable_creation_tool_failed",
            "catalog_identifier": catalog_identifier,
            "error": str(e)
        })
        return {
            'success': False,
            'error': f'Failed to create batch variables: {str(e)}'
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
        add_reference_variable,
        add_multiple_variables,
        # Variable set tools
        link_variable_set_to_catalog,
        # Publishing tool
        publish_catalog_item,
        # Variable types tool
        get_servicenow_variable_types
    ] 