"""
ServiceNow API Integration for Teams Agent Bot.

This module provides real ServiceNow API integration for catalog item creation
and management using the ServiceNow REST API.
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin

from config.settings import settings
from utils.logger import get_logger, log_function_call, log_function_result, log_error_with_context

logger = get_logger(__name__)


class ServiceNowAPI:
    """ServiceNow API client for catalog operations."""
    
    def __init__(self, instance_url: str, username: str, password: str):
        """
        Initialize ServiceNow API client.
        
        Args:
            instance_url: ServiceNow instance URL (e.g., 'https://yourcompany.service-now.com')
            username: ServiceNow username
            password: ServiceNow password or API key
        """
        self.instance_url = instance_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info({
            "event": "servicenow_api_initialized",
            "instance_url": instance_url,
            "username": username
        })
    
    def get_catalog_by_name_or_number(self, catalog_identifier: str) -> Dict[str, Any]:
        """Get catalog item by name or number."""
        try:
            # Try to find by name first
            endpoint = urljoin(self.instance_url, f'/api/now/table/sc_cat_item?sysparm_query=name={catalog_identifier}')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') and len(result['result']) > 0:
                    catalog = result['result'][0]
                    return {
                        'success': True,
                        'catalog_id': catalog['sys_id'],
                        'catalog_name': catalog['name'],
                        'catalog_number': catalog.get('number', ''),
                        'data': catalog
                    }
            
            # If not found by name, try by number
            endpoint = urljoin(self.instance_url, f'/api/now/table/sc_cat_item?sysparm_query=number={catalog_identifier}')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') and len(result['result']) > 0:
                    catalog = result['result'][0]
                    return {
                        'success': True,
                        'catalog_id': catalog['sys_id'],
                        'catalog_name': catalog['name'],
                        'catalog_number': catalog.get('number', ''),
                        'data': catalog
                    }
            
            return {
                'success': False,
                'error': f'Catalog not found: {catalog_identifier}'
            }
            
        except Exception as e:
            logger.error({
                "event": "servicenow_catalog_lookup_failed",
                "catalog_identifier": catalog_identifier,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to lookup catalog: {str(e)}'
            }

    def _resolve_catalog_id(self, catalog_identifier: str) -> str:
        """Smart detection: resolve catalog_identifier to catalog_id."""
        # If it looks like a sys_id (32 alphanumeric characters), use as catalog_id
        if len(catalog_identifier) == 32 and catalog_identifier.isalnum():
            return catalog_identifier
        
        # Otherwise, look it up by name or number
        result = self.get_catalog_by_name_or_number(catalog_identifier)
        if not result['success']:
            raise ValueError(result['error'])
        
        return result['catalog_id']

    def create_catalog_item(self, name: str, short_description: str, long_description: str, category: str, catalog_type: str = 'item') -> Dict[str, Any]:
        """Create a new catalog item (without variables)."""
        try:
            # Map category and catalog type
            mapped_category = self._map_category(category)
            mapped_catalog_type = self._map_catalog_type(catalog_type)
            
            # Create catalog item payload
            payload = {
                'name': name,
                'short_description': short_description,
                'description': long_description,  # ServiceNow uses 'description' for long description
                'category': mapped_category,
                'type': mapped_catalog_type,
                'active': 'true',
                'order': '100'
            }
            
            endpoint = urljoin(self.instance_url, '/api/now/table/sc_cat_item')
            
            # Log the API call details
            logger.info({
                "event": "servicenow_api_call",
                "method": "POST",
                "endpoint": endpoint,
                "payload": payload,
                "mapped_category": mapped_category,
                "mapped_catalog_type": mapped_catalog_type,
                "original_category": category,
                "original_catalog_type": catalog_type
            })
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                catalog_id = result['result']['sys_id']
                
                logger.info({
                    "event": "servicenow_catalog_created",
                    "catalog_id": catalog_id,
                    "catalog_name": name,
                    "response_status": response.status_code,
                    "response_body": result
                })
                
                return {
                    'success': True,
                    'catalog_id': catalog_id,
                    'catalog_name': name,
                    'message': f"Catalog item '{name}' created successfully",
                    'details': {
                        'name': name,
                        'sys_id': catalog_id,
                        'number': result['result'].get('number', ''),
                        'status': 'active'
                    }
                }
            else:
                logger.error({
                    "event": "servicenow_catalog_creation_failed",
                    "catalog_name": name,
                    "status_code": response.status_code,
                    "response_text": response.text,
                    "response_headers": dict(response.headers)
                })
                
                return {
                    'success': False,
                    'error': f'Failed to create catalog item: {response.text}'
                }
                
        except Exception as e:
            logger.error({
                "event": "servicenow_catalog_creation_failed",
                "catalog_name": name,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to create catalog item: {str(e)}'
            }

    def publish_catalog_item(self, catalog_identifier: str) -> Dict[str, Any]:
        """Publish a catalog item."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            return self._publish_catalog_item(catalog_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_catalog_item(self, catalog_identifier: str) -> Dict[str, Any]:
        """Get catalog item details."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            
            endpoint = urljoin(self.instance_url, f'/api/now/table/sc_cat_item/{catalog_id}')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'data': result['result']
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to get catalog item: {response.text}'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_catalog_items(self, search_term: str = None, limit: int = 10) -> Dict[str, Any]:
        """Search for catalog items by name or description."""
        try:
            # Build query based on search term
            if search_term:
                query = f"nameLIKE{search_term}^ORshort_descriptionLIKE{search_term}^ORdescriptionLIKE{search_term}"
            else:
                query = "active=true"
            
            endpoint = urljoin(self.instance_url, f'/api/now/table/sc_cat_item?sysparm_query={query}&sysparm_limit={limit}&sysparm_display_value=true')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                catalogs = result.get('result', [])
                
                # Format the results
                formatted_catalogs = []
                for catalog in catalogs:
                    formatted_catalogs.append({
                        'sys_id': catalog.get('sys_id', ''),
                        'name': catalog.get('name', ''),
                        'number': catalog.get('number', ''),
                        'short_description': catalog.get('short_description', ''),
                        'long_description': catalog.get('description', ''),  # ServiceNow uses 'description' field
                        'category': catalog.get('category', ''),
                        'type': catalog.get('type', ''),
                        'active': catalog.get('active', False),
                        'published': catalog.get('published', False)
                    })
                
                return {
                    'success': True,
                    'catalogs': formatted_catalogs,
                    'count': len(formatted_catalogs),
                    'search_term': search_term
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to search catalog items: {response.text}'
                }
                
        except Exception as e:
            logger.error({
                "event": "servicenow_catalog_search_failed",
                "search_term": search_term,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to search catalog items: {str(e)}'
            }

    def list_catalog_items(self, category: str = None, limit: int = 20) -> Dict[str, Any]:
        """List catalog items, optionally filtered by category."""
        try:
            # Build query
            if category:
                # First get the category sys_id
                category_id = self._map_category(category)
                if category_id:
                    query = f"active=true^category={category_id}"
                else:
                    query = "active=true"
            else:
                query = "active=true"
            
            endpoint = urljoin(self.instance_url, f'/api/now/table/sc_cat_item?sysparm_query={query}&sysparm_limit={limit}&sysparm_display_value=true')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                catalogs = result.get('result', [])
                
                # Format the results
                formatted_catalogs = []
                for catalog in catalogs:
                    formatted_catalogs.append({
                        'sys_id': catalog.get('sys_id', ''),
                        'name': catalog.get('name', ''),
                        'number': catalog.get('number', ''),
                        'short_description': catalog.get('short_description', ''),
                        'long_description': catalog.get('description', ''),  # ServiceNow uses 'description' field
                        'category': catalog.get('category', ''),
                        'type': catalog.get('type', ''),
                        'active': catalog.get('active', False),
                        'published': catalog.get('published', False)
                    })
                
                return {
                    'success': True,
                    'catalogs': formatted_catalogs,
                    'count': len(formatted_catalogs),
                    'category': category
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to list catalog items: {response.text}'
                }
                
        except Exception as e:
            logger.error({
                "event": "servicenow_catalog_list_failed",
                "category": category,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to list catalog items: {str(e)}'
            }

    def create_string_variable(self, catalog_identifier: str, name: str, label: str, required: bool = False, 
                             default_value: str = None, help_text: str = None) -> Dict[str, Any]:
        """Create a string variable for a catalog item."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            
            payload = {
                'cat_item': catalog_id,
                'type': '6',  # String/Single line text
                'name': name,
                'question_text': label,
                'mandatory': 'true' if required else 'false',
                'active': 'true',
                'order': '100'
            }
            
            if help_text:
                payload['help_text'] = help_text
            if default_value:
                payload['default_value'] = default_value
            
            endpoint = urljoin(self.instance_url, '/api/now/table/item_option_new')
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                variable_id = result['result']['sys_id']
                
                logger.info({
                    "event": "servicenow_string_variable_created",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "variable_id": variable_id
                })
                
                return {
                    'success': True,
                    'variable_id': variable_id,
                    'variable_name': name,
                    'catalog_id': catalog_id,
                    'message': f"String variable '{name}' created successfully"
                }
            else:
                logger.error({
                    "event": "servicenow_string_variable_creation_failed",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "status_code": response.status_code,
                    "response_text": response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to create string variable: {response.text}'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error({
                "event": "servicenow_string_variable_creation_failed",
                "catalog_identifier": catalog_identifier,
                "variable_name": name,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to create string variable: {str(e)}'
            }

    def create_boolean_variable(self, catalog_identifier: str, name: str, label: str, required: bool = False,
                              default_value: bool = False, help_text: str = None) -> Dict[str, Any]:
        """Create a boolean variable for a catalog item."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            
            payload = {
                'cat_item': catalog_id,
                'type': '1',  # Boolean/Yes-No
                'name': name,
                'question_text': label,
                'mandatory': 'true' if required else 'false',
                'active': 'true',
                'order': '100',
                'default_value': 'true' if default_value else 'false'
            }
            
            if help_text:
                payload['help_text'] = help_text
            
            endpoint = urljoin(self.instance_url, '/api/now/table/item_option_new')
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                variable_id = result['result']['sys_id']
                
                logger.info({
                    "event": "servicenow_boolean_variable_created",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "variable_id": variable_id
                })
                
                return {
                    'success': True,
                    'variable_id': variable_id,
                    'variable_name': name,
                    'catalog_id': catalog_id,
                    'message': f"Boolean variable '{name}' created successfully"
                }
            else:
                logger.error({
                    "event": "servicenow_boolean_variable_creation_failed",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "status_code": response.status_code,
                    "response_text": response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to create boolean variable: {response.text}'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error({
                "event": "servicenow_boolean_variable_creation_failed",
                "catalog_identifier": catalog_identifier,
                "variable_name": name,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to create boolean variable: {str(e)}'
            }

    def create_choice_variable(self, catalog_identifier: str, name: str, label: str, choices: List[str],
                             required: bool = False, default_value: str = None, help_text: str = None) -> Dict[str, Any]:
        """Create a choice variable (select box) for a catalog item."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            
            payload = {
                'cat_item': catalog_id,
                'type': '5',  # Select Box/Dropdown
                'name': name,
                'question_text': label,
                'mandatory': 'true' if required else 'false',
                'active': 'true',
                'order': '100'
            }
            
            if help_text:
                payload['help_text'] = help_text
            
            if default_value:
                payload['default_value'] = default_value
            
            endpoint = urljoin(self.instance_url, '/api/now/table/item_option_new')
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                variable_id = result['result']['sys_id']
                
                # Create choices for the variable
                choices_created = self._create_choices_for_variable(name, choices, variable_id)
                
                logger.info({
                    "event": "servicenow_choice_variable_created",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "variable_id": variable_id,
                    "choices_created": choices_created
                })
                
                return {
                    'success': True,
                    'variable_id': variable_id,
                    'variable_name': name,
                    'catalog_id': catalog_id,
                    'choices_created': choices_created,
                    'message': f"Select box variable '{name}' created successfully with {len(choices)} choices"
                }
            else:
                logger.error({
                    "event": "servicenow_choice_variable_creation_failed",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "status_code": response.status_code,
                    "response_text": response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to create select box variable: {response.text}'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error({
                "event": "servicenow_choice_variable_creation_failed",
                "catalog_identifier": catalog_identifier,
                "variable_name": name,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to create select box variable: {str(e)}'
            }

    def create_multiple_choice_variable(self, catalog_identifier: str, name: str, label: str, choices: List[str],
                                      required: bool = False, default_value: str = None, help_text: str = None) -> Dict[str, Any]:
        """Create a multiple choice variable (radio buttons) for a catalog item."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            
            payload = {
                'cat_item': catalog_id,
                'type': '3',  # Multiple Choice/Radio Buttons
                'name': name,
                'question_text': label,
                'mandatory': 'true' if required else 'false',
                'active': 'true',
                'order': '100'
            }
            
            if help_text:
                payload['help_text'] = help_text
            
            if default_value:
                payload['default_value'] = default_value
            
            endpoint = urljoin(self.instance_url, '/api/now/table/item_option_new')
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                variable_id = result['result']['sys_id']
                
                # Create choices for the variable
                choices_created = self._create_choices_for_variable(name, choices, variable_id)
                
                logger.info({
                    "event": "servicenow_multiple_choice_variable_created",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "variable_id": variable_id,
                    "choices_created": choices_created
                })
                
                return {
                    'success': True,
                    'variable_id': variable_id,
                    'variable_name': name,
                    'catalog_id': catalog_id,
                    'choices_created': choices_created,
                    'message': f"Multiple choice variable '{name}' created successfully with {len(choices)} choices"
                }
            else:
                logger.error({
                    "event": "servicenow_multiple_choice_variable_creation_failed",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "status_code": response.status_code,
                    "response_text": response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to create multiple choice variable: {response.text}'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error({
                "event": "servicenow_multiple_choice_variable_creation_failed",
                "catalog_identifier": catalog_identifier,
                "variable_name": name,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to create multiple choice variable: {str(e)}'
            }

    def create_date_variable(self, catalog_identifier: str, name: str, label: str, required: bool = False,
                           default_value: str = None, help_text: str = None) -> Dict[str, Any]:
        """Create a date variable for a catalog item."""
        try:
            catalog_id = self._resolve_catalog_id(catalog_identifier)
            
            payload = {
                'cat_item': catalog_id,
                'type': '9',  # Date
                'name': name,
                'question_text': label,
                'mandatory': 'true' if required else 'false',
                'active': 'true',
                'order': '100'
            }
            
            if help_text:
                payload['help_text'] = help_text
            
            if default_value:
                payload['default_value'] = default_value
            
            endpoint = urljoin(self.instance_url, '/api/now/table/item_option_new')
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                variable_id = result['result']['sys_id']
                
                logger.info({
                    "event": "servicenow_date_variable_created",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "variable_id": variable_id
                })
                
                return {
                    'success': True,
                    'variable_id': variable_id,
                    'variable_name': name,
                    'catalog_id': catalog_id,
                    'message': f"Date variable '{name}' created successfully"
                }
            else:
                logger.error({
                    "event": "servicenow_date_variable_creation_failed",
                    "catalog_id": catalog_id,
                    "variable_name": name,
                    "status_code": response.status_code,
                    "response_text": response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to create date variable: {response.text}'
                }
                
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error({
                "event": "servicenow_date_variable_creation_failed",
                "catalog_identifier": catalog_identifier,
                "variable_name": name,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to create date variable: {str(e)}'
            }
    
    def _create_catalog_variables(self, catalog_id: str, variables: List[Dict[str, Any]]) -> bool:
        """
        Create variables for a catalog item.
        
        Args:
            catalog_id: The catalog item sys_id
            variables: List of variable data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use item_option_new table - this is the correct table for catalog variables
            endpoint = urljoin(self.instance_url, '/api/now/table/item_option_new')
            
            for i, var in enumerate(variables):
                # Use correct ServiceNow field names for item_option_new (matching reference code)
                payload = {
                    'cat_item': catalog_id,  # Link directly during creation
                    'type': self._map_variable_type(var['type']),  # Use mapped type for all variables
                    'name': var['name'],
                    'question_text': var['label'],  # Use question_text for display label
                    'mandatory': 'true' if var.get('required', False) else 'false',
                    'active': 'true',
                    'order': str(100 + (i * 10))  # Increment order for each variable
                }
                
                # Add optional fields if provided
                if var.get('help_text'):
                    payload['help_text'] = var['help_text']
                # Only add default value for non-choice variables
                if var.get('default_value') and var['type'] not in ['choice', 'multiple_choice']:
                    payload['default_value'] = var['default_value']
                
                # For choice variables, keep it simple like reference code
                # No extra fields needed in the variable payload
                

                
                # Add boolean-specific fields for single checkbox display
                if var['type'] == 'boolean':
                    # Set default value for boolean
                    if var.get('default_value'):
                        payload['default_value'] = var['default_value']
                    else:
                        payload['default_value'] = 'false'
                
                # Add string-specific fields for text input
                if var['type'] == 'string':
                    # For string type, ensure it displays as text input, not dropdown
                    payload['max_length'] = var.get('max_length', 255)
                    # Explicitly set display type to ensure text input
                    payload['display_type'] = '1'  # Text input
                
                # Add integer-specific fields for number input
                if var['type'] == 'integer':
                    if var.get('min_value') is not None:
                        payload['min_value'] = var['min_value']
                    if var.get('max_value') is not None:
                        payload['max_value'] = var['max_value']
                
                # Add validation constraints
                if var.get('max_length'):
                    payload['max_length'] = var['max_length']
                
                if var.get('min_value') is not None:
                    payload['min_value'] = var['min_value']
                
                if var.get('max_value') is not None:
                    payload['max_value'] = var['max_value']
                
                response = self.session.post(endpoint, json=payload, timeout=30)
                
                if response.status_code != 201:
                    logger.error({
                        "event": "servicenow_variable_creation_failed",
                        "variable_name": var['name'],
                        "status_code": response.status_code,
                        "response_text": response.text
                    })
                    return False
                
                # If this is a choice variable, create the choices in question_choice table
                if var['type'] in ['choice', 'multiple_choice'] and var.get('choices'):
                    variable_result = response.json()
                    variable_sys_id = variable_result['result']['sys_id']
                    self._create_choices_for_variable(var['name'], var['choices'], variable_sys_id)
                

            
            return True
            
        except Exception as e:
            logger.error({
                "event": "servicenow_variables_creation_failed",
                "error": str(e),
                "catalog_id": catalog_id
            })
            return False
    
    def _create_choices_for_variable(self, variable_name: str, choices: List[str], variable_sys_id: str) -> bool:
        """Create choices for a choice variable using question_choice table (working approach)."""
        try:
            endpoint = urljoin(self.instance_url, '/api/now/table/question_choice')
            
            for i, choice in enumerate(choices):
                choice_data = {
                    'question': variable_sys_id,  # Reference to the variable's sys_id
                    'value': choice,  # Use the actual choice text
                    'text': choice,  # Display text
                    'order': str(i * 100),
                    'active': 'true'
                }
                
                response = self.session.post(endpoint, json=choice_data, timeout=30)
                
                if response.status_code != 201:
                    logger.error({
                        "event": "servicenow_choice_creation_failed",
                        "variable_name": variable_name,
                        "choice": choice,
                        "status_code": response.status_code,
                        "response_text": response.text
                    })
                    return False
                
                logger.info({
                    "event": "servicenow_choice_created",
                    "variable_name": variable_name,
                    "choice": choice
                })
            
            return True
            
        except Exception as e:
            logger.error({
                "event": "servicenow_choices_creation_failed",
                "variable_name": variable_name,
                "error": str(e)
            })
            return False
    
    def _publish_catalog_item(self, catalog_id: str) -> Dict[str, Any]:
        """Publish a catalog item to make it visible in the Service Catalog."""
        try:
            # ServiceNow publish endpoint
            endpoint = urljoin(self.instance_url, f'/api/now/table/sc_cat_item/{catalog_id}')
            
            # Update the catalog item to set it as published
            publish_data = {
                'active': True,
                'published': True,
                'order': 100
            }
            
            # Log the publish API call
            logger.info({
                "event": "servicenow_publish_api_call",
                "method": "PATCH",
                "endpoint": endpoint,
                "catalog_id": catalog_id,
                "payload": publish_data
            })
            
            response = self.session.patch(endpoint, json=publish_data, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info({
                    "event": "servicenow_catalog_published",
                    "catalog_id": catalog_id
                })
                return {
                    'success': True,
                    'catalog_id': catalog_id,
                    'message': f"Catalog item published successfully"
                }
            else:
                logger.warning({
                    "event": "servicenow_catalog_publish_failed",
                    "catalog_id": catalog_id,
                    "status_code": response.status_code,
                    "response_text": response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to publish catalog item: {response.text}'
                }
                
        except Exception as e:
            logger.error({
                "event": "servicenow_catalog_publish_error",
                "catalog_id": catalog_id,
                "error": str(e)
            })
            return {
                'success': False,
                'error': f'Failed to publish catalog item: {str(e)}'
            }
    
    def _map_category(self, category: str) -> str:
        """Map our category to ServiceNow category sys_id."""
        # Dynamically fetch categories from ServiceNow
        try:
            endpoint = urljoin(self.instance_url, '/api/now/table/sc_category?sysparm_limit=100&sysparm_query=active=true')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get('result', [])
                
                # Find category by title (case-insensitive)
                # First try exact match
                for cat in categories:
                    cat_title = cat.get('title', '').lower()
                    if category.lower() == cat_title:
                        return cat.get('sys_id', '')
                
                # If no exact match, try partial match but be more careful
                for cat in categories:
                    cat_title = cat.get('title', '').lower()
                    category_lower = category.lower()
                    
                    # Check if the category name is a word boundary match
                    # This prevents "Hardware" from matching "Hardware Asset"
                    if (category_lower in cat_title and 
                        (cat_title.startswith(category_lower + ' ') or 
                         cat_title.endswith(' ' + category_lower) or
                         cat_title == category_lower)):
                        return cat.get('sys_id', '')
                
                # If no exact match, return first available category
                if categories:
                    logger.info(f"Category '{category}' not found, using first available category")
                    return categories[0].get('sys_id', '')
            
            logger.warning(f"Failed to fetch categories, using fallback")
            return ''
            
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return ''
    
    def _map_catalog_type(self, catalog_type: str) -> str:
        """Map our catalog type to ServiceNow type."""
        type_mapping = {
            'service': 'service',
            'hardware': 'hardware',
            'employee': 'employee'
        }
        return type_mapping.get(catalog_type, 'service')
    
    def _map_variable_type(self, var_type: str) -> str:
        """Map our variable types to ServiceNow variable types."""
        # Based on actual ServiceNow data analysis and reference code
        type_mapping = {
            'string': '6',           # String/Single line text
            'textarea': '2',         # Textarea
            'integer': '5',          # Integer/Number
            'decimal': '6',          # Decimal/Number
            'boolean': '1',          # Boolean/Yes-No
            'date': '9',             # Date
            'datetime': '10',        # Date/Time
            'email': '26',           # Email
            'url': '11',             # URL
            'reference': '8',        # Reference
            'choice': '5',           # Select Box/Dropdown (user selects from dropdown)
            'multiple_choice': '3'   # Multiple Choice/Radio (from reference code)
        }
        return type_mapping.get(var_type, '6')  # Default to String

    # ---------- Wrapper Methods for Tools ----------
    def add_string_variable(self, catalog_identifier: str, variable_name: str, question_text: str, default_value: str = None) -> Dict[str, Any]:
        """
        Wrapper method for add_string_variable tool.
        
        Args:
            catalog_identifier: Catalog ID or name
            variable_name: Name of the variable
            question_text: Display text for the variable
            default_value: Optional default value
            
        Returns:
            Dict containing the creation result
        """
        return self.create_string_variable(
            catalog_identifier=catalog_identifier,
            name=variable_name,
            label=question_text,
            default_value=default_value
        )

    def add_boolean_variable(self, catalog_identifier: str, variable_name: str, question_text: str, default_value: bool = False) -> Dict[str, Any]:
        """
        Wrapper method for add_boolean_variable tool.
        
        Args:
            catalog_identifier: Catalog ID or name
            variable_name: Name of the variable
            question_text: Display text for the variable
            default_value: Default boolean value
            
        Returns:
            Dict containing the creation result
        """
        return self.create_boolean_variable(
            catalog_identifier=catalog_identifier,
            name=variable_name,
            label=question_text,
            default_value=default_value
        )

    def add_multiple_choice_variable(self, catalog_identifier: str, variable_name: str, question_text: str, choices: List[str], default_value: str = None) -> Dict[str, Any]:
        """
        Wrapper method for add_multiple_choice_variable tool.
        
        Args:
            catalog_identifier: Catalog ID or name
            variable_name: Name of the variable
            question_text: Display text for the variable
            choices: List of choice options
            default_value: Optional default choice
            
        Returns:
            Dict containing the creation result
        """
        return self.create_multiple_choice_variable(
            catalog_identifier=catalog_identifier,
            name=variable_name,
            label=question_text,
            choices=choices,
            default_value=default_value
        )

    def add_date_variable(self, catalog_identifier: str, variable_name: str, question_text: str, default_value: str = None) -> Dict[str, Any]:
        """
        Wrapper method for add_date_variable tool.
        
        Args:
            catalog_identifier: Catalog ID or name
            variable_name: Name of the variable
            question_text: Display text for the variable
            default_value: Optional default date (YYYY-MM-DD format)
            
        Returns:
            Dict containing the creation result
        """
        return self.create_date_variable(
            catalog_identifier=catalog_identifier,
            name=variable_name,
            label=question_text,
            default_value=default_value
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the ServiceNow API connection.
        
        Returns:
            Dict containing connection test result
        """
        try:
            endpoint = urljoin(self.instance_url, '/api/now/table/sc_cat_item?sysparm_limit=1')
            response = self.session.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "ServiceNow API connection successful",
                    "instance_url": self.instance_url
                }
            else:
                return {
                    "success": False,
                    "error": f"ServiceNow API test failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"ServiceNow API connection failed: {str(e)}"
            }
    
    def get_available_categories(self) -> Dict[str, Any]:
        """
        Get available ServiceNow categories.
        
        Returns:
            Dict containing available categories
        """
        try:
            # Query the sc_category table which contains the actual category information
            endpoint = urljoin(self.instance_url, '/api/now/table/sc_category?sysparm_limit=100&sysparm_query=active=true')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get('result', [])
                
                # Format categories for display
                formatted_categories = []
                for cat in categories:
                    formatted_categories.append({
                        'title': cat.get('title', 'N/A'),
                        'sys_id': cat.get('sys_id', ''),
                        'description': cat.get('description', ''),
                        'active': cat.get('active', False),
                        'parent': cat.get('parent', ''),
                        'level': cat.get('level', 0)
                    })
                
                return {
                    "success": True,
                    "categories": formatted_categories,
                    "count": len(formatted_categories)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch categories: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching categories: {str(e)}"
            }
    
    def get_available_catalog_types(self) -> Dict[str, Any]:
        """
        Get available ServiceNow catalog types.
        
        Returns:
            Dict containing available catalog types
        """
        try:
            # Query existing catalog items to see what types are actually used
            endpoint = urljoin(self.instance_url, '/api/now/table/sc_cat_item?sysparm_limit=100&sysparm_fields=type')
            response = self.session.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('result', [])
                
                # Extract unique catalog types
                catalog_types = set()
                for item in items:
                    item_type = item.get('type', '')
                    if item_type:
                        catalog_types.add(item_type)
                
                # Get type descriptions from sys_dictionary if possible
                type_descriptions = {
                    'service': 'Service requests (password reset, access requests, etc.)',
                    'hardware': 'Hardware requests (laptops, phones, monitors, etc.)',
                    'employee': 'Employee-related requests (onboarding, offboarding, etc.)',
                    'software': 'Software requests (licenses, applications, etc.)',
                    'other': 'Other types of requests'
                }
                
                # Format catalog types for display
                formatted_types = []
                for cat_type in sorted(catalog_types):
                    formatted_types.append({
                        'type': cat_type,
                        'description': type_descriptions.get(cat_type, f'Catalog type: {cat_type}'),
                        'count': sum(1 for item in items if item.get('type') == cat_type)
                    })
                
                return {
                    "success": True,
                    "catalog_types": formatted_types,
                    "count": len(formatted_types),
                    "total_items": len(items)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch catalog types: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching catalog types: {str(e)}"
            }


# Global ServiceNow API client instance
_servicenow_client = None


def get_servicenow_client() -> Optional[ServiceNowAPI]:
    """
    Get the global ServiceNow API client instance.
    
    Returns:
        ServiceNowAPI client if configured, None otherwise
    """
    global _servicenow_client
    
    # If client is already initialized, return it
    if _servicenow_client is not None:
        return _servicenow_client
    
    # Check if ServiceNow is configured
    if not settings.servicenow.instance_url:
        logger.info("ServiceNow not configured - will use mock mode")
        return None
    
    # Initialize client with settings
    try:
        if settings.servicenow.auth_method == "basic":
            if not settings.servicenow.username or not settings.servicenow.password:
                logger.warning("ServiceNow basic auth configured but username/password missing")
                return None
            
            _servicenow_client = ServiceNowAPI(
                instance_url=settings.servicenow.instance_url,
                username=settings.servicenow.username,
                password=settings.servicenow.password
            )
        elif settings.servicenow.auth_method == "oauth":
            if not settings.servicenow.client_id or not settings.servicenow.client_secret:
                logger.warning("ServiceNow OAuth configured but client_id/client_secret missing")
                return None
            
            # TODO: Implement OAuth authentication
            logger.warning("ServiceNow OAuth authentication not yet implemented")
            return None
        else:
            logger.warning(f"Unknown ServiceNow auth method: {settings.servicenow.auth_method}")
            return None
        
        logger.info("ServiceNow API client initialized successfully")
        return _servicenow_client
        
    except Exception as e:
        logger.error(f"Failed to initialize ServiceNow API client: {e}")
        return None


def initialize_servicenow_client(instance_url: str, username: str, password: str) -> ServiceNowAPI:
    """
    Initialize the global ServiceNow API client.
    
    Args:
        instance_url: ServiceNow instance URL
        username: ServiceNow username
        password: ServiceNow password or API key
        
    Returns:
        Initialized ServiceNowAPI client
    """
    global _servicenow_client
    _servicenow_client = ServiceNowAPI(instance_url, username, password)
    return _servicenow_client 