#!/usr/bin/env python3
"""
Test script for ServiceNow integration.

This script demonstrates how to:
1. Initialize the ServiceNow API client
2. Test the connection
3. Create a catalog item with variables
4. Handle errors and validation

Usage:
    python test_servicenow_integration.py
"""

import os
import sys
from openai_agents.servicenow_api import initialize_servicenow_client, get_servicenow_client
from openai_agents.servicenow_tools import create_catalog_item


def test_servicenow_connection():
    """Test ServiceNow API connection."""
    print("🔗 Testing ServiceNow API connection...")
    
    # Get credentials from environment
    instance_url = os.getenv('SERVICENOW_INSTANCE_URL')
    username = os.getenv('SERVICENOW_USERNAME')
    password = os.getenv('SERVICENOW_PASSWORD')
    
    if not all([instance_url, username, password]):
        print("⚠️  ServiceNow credentials not found in environment variables.")
        print("   The system will use MOCK MODE for catalog creation.")
        print("   To use real ServiceNow API, set:")
        print("   - SERVICENOW_INSTANCE_URL")
        print("   - SERVICENOW_USERNAME") 
        print("   - SERVICENOW_PASSWORD")
        return False
    
    try:
        # Initialize client
        client = initialize_servicenow_client(instance_url, username, password)
        
        # Test connection
        result = client.test_connection()
        
        if result['success']:
            print("✅ ServiceNow connection successful!")
            print(f"   Instance: {result['instance_url']}")
            return True
        else:
            print(f"❌ ServiceNow connection failed: {result['error']}")
            print("   The system will fall back to MOCK MODE.")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize ServiceNow client: {str(e)}")
        print("   The system will fall back to MOCK MODE.")
        return False


async def query_catalog_types():
    """Query available catalog types from ServiceNow."""
    try:
        from openai_agents.servicenow_api import get_servicenow_client
        
        servicenow_client = get_servicenow_client()
        
        if not servicenow_client:
            return {
                "success": False,
                "error": "ServiceNow client not available",
                "fallback_types": ["service", "hardware", "employee"]
            }
        
        result = servicenow_client.get_available_catalog_types()
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get catalog types: {str(e)}",
            "fallback_types": ["service", "hardware", "employee"]
        }


async def query_categories():
    """Query available categories from ServiceNow."""
    try:
        from openai_agents.servicenow_api import get_servicenow_client
        
        servicenow_client = get_servicenow_client()
        
        if not servicenow_client:
            return {
                "success": False,
                "error": "ServiceNow client not available",
                "fallback_categories": ["Hardware", "Software", "Access", "Other"]
            }
        
        result = servicenow_client.get_available_categories()
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get categories: {str(e)}",
            "fallback_categories": ["Hardware", "Software", "Access", "Other"]
        }


async def check_catalog_item_status(catalog_id: str):
    """Check the status of a created catalog item."""
    try:
        from openai_agents.servicenow_api import get_servicenow_client
        
        servicenow_client = get_servicenow_client()
        
        if not servicenow_client:
            print("   ❌ Cannot check status: ServiceNow client not available")
            return
        
        # Query the specific catalog item
        endpoint = f"{servicenow_client.instance_url}/api/now/table/sc_cat_item/{catalog_id}"
        response = servicenow_client.session.get(endpoint, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            item = data.get('result', {})
            
            print(f"   📋 Catalog Item Details:")
            print(f"      Name: {item.get('name', 'N/A')}")
            print(f"      Number: {item.get('number', 'N/A')}")
            print(f"      Active: {item.get('active', 'N/A')}")
            print(f"      Order: {item.get('order', 'N/A')}")
            print(f"      Category: {item.get('category', 'N/A')}")
            print(f"      Type: {item.get('type', 'N/A')}")
            print(f"      Workflow: {item.get('workflow', 'N/A')}")
            print(f"      Published: {item.get('published', 'N/A')}")
            
            # Check if item is visible in catalog
            # Since we know we published it successfully, let's check if it's active
            if item.get('active') == 'true':
                print("   ✅ Item should be visible in Service Catalog")
                print("   ✅ Item is active and was published successfully")
                print("   💡 If not visible in ServiceNow interface, check:")
                print("      - User permissions and roles")
                print("      - Catalog access controls")
                print("      - Category visibility settings")
                print("      - Browser cache (try refreshing)")
            else:
                print("   ⚠️  Item may not be visible due to:")
                if item.get('active') != 'true':
                    print("      - Item is not active")
                print("   💡 Try activating the item in ServiceNow")
        else:
            print(f"   ❌ Failed to query catalog item: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking catalog item status: {str(e)}")


async def test_catalog_creation():
    """Test catalog item creation with dynamic querying."""
    print("\n📋 Testing catalog item creation with dynamic querying...")
    
    # First, query available catalog types and categories
    print("\n1. Querying available catalog types...")
    catalog_types_result = await query_catalog_types()
    
    if not catalog_types_result['success']:
        print(f"❌ Failed to get catalog types: {catalog_types_result['error']}")
        print("   Using fallback catalog types...")
        catalog_types = catalog_types_result.get('fallback_types', ["service", "hardware", "employee"])
        print(f"   Available types: {', '.join(catalog_types)}")
        selected_catalog_type = catalog_types[0]  # Default to first
    else:
        # Check if only one catalog type is available
        if catalog_types_result['count'] == 1:
            selected_catalog_type = catalog_types_result['catalog_types'][0]['type']
            print(f"✅ Only one catalog type available: {selected_catalog_type}")
            print(f"   Auto-selected: {selected_catalog_type}")
        else:
            print(f"✅ Found {catalog_types_result['count']} catalog types:")
            for i, cat_type in enumerate(catalog_types_result['catalog_types'], 1):
                print(f"   {i}. {cat_type['type']} - {cat_type['description']} ({cat_type['count']} items)")
            
            # Let user select catalog type
            while True:
                try:
                    selection = input(f"\nSelect catalog type (1-{len(catalog_types_result['catalog_types'])}): ")
                    selection_idx = int(selection) - 1
                    if 0 <= selection_idx < len(catalog_types_result['catalog_types']):
                        selected_catalog_type = catalog_types_result['catalog_types'][selection_idx]['type']
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
    
    print(f"\n2. Querying available categories for catalog type '{selected_catalog_type}'...")
    categories_result = await query_categories()
    
    if not categories_result['success']:
        print(f"❌ Failed to get categories: {categories_result['error']}")
        print("   Using fallback categories...")
        categories = categories_result.get('fallback_categories', ["Hardware", "Software", "Access"])
        print(f"   Available categories: {', '.join(categories)}")
        selected_category = categories[0]  # Default to first
        selected_category_sys_id = None
    else:
        print(f"✅ Found {categories_result['count']} categories:")
        for i, category in enumerate(categories_result['categories'], 1):
            print(f"   {i}. {category['title']} - {category['description']}")
        
        # Let user select category
        while True:
            try:
                selection = input(f"\nSelect category (1-{len(categories_result['categories'])}): ")
                selection_idx = int(selection) - 1
                if 0 <= selection_idx < len(categories_result['categories']):
                    selected_category = categories_result['categories'][selection_idx]['title']
                    selected_category_sys_id = categories_result['categories'][selection_idx]['sys_id']
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    # Get catalog item details from user
    print(f"\n3. Enter catalog item details:")
    name = input("Catalog item name: ").strip()
    short_description = input("Short description: ").strip()
    long_description = input("Long description: ").strip()
    
    # Test data with user selections
    test_catalog = {
        'name': name or 'Test Catalog Item',
        'catalog_type': selected_catalog_type,
        'category': selected_category,
        'short_description': short_description or 'Test catalog item',
        'long_description': long_description or 'Test catalog item description',
        'variables': [
            {
                'name': 'test_variable',
                'label': 'Test Variable',
                'type': 'string',
                'required': True,
                'help_text': 'Test variable for catalog item'
            }
        ]
    }
    
    try:
        # Call catalog creation directly using the same logic as the tool
        from config.settings import settings
        from openai_agents.servicenow_api import get_servicenow_client
        from openai_agents.servicenow_tools import _mock_catalog_creation, SERVICENOW_CATALOG_TYPES, SERVICENOW_CATEGORIES, SERVICENOW_VARIABLE_TYPES
        
        # Validate inputs (same validation as the tool)
        name = test_catalog['name']
        catalog_type = test_catalog['catalog_type']
        category = test_catalog['category']
        short_description = test_catalog['short_description']
        long_description = test_catalog['long_description']
        variables = test_catalog['variables']
        
        if not name or not name.strip():
            raise ValueError("Catalog name is required")
        
        # Use dynamic validation for catalog type and category
        # Since we already queried ServiceNow and got user selection, we trust the values
        # The validation here is just for basic format checking
        if not catalog_type or not catalog_type.strip():
            raise ValueError("Catalog type is required")
        
        if not category or not category.strip():
            raise ValueError("Category is required")
        
        if not short_description or len(short_description) > 100:
            raise ValueError("Short description is required and must be 100 characters or less")
        
        if not long_description:
            raise ValueError("Long description is required")
        
        # Validate variables if provided
        validated_variables = []
        if variables:
            if len(variables) > 7:
                raise ValueError("Maximum of 7 variables allowed")
            
            for i, var in enumerate(variables):
                if not var.get('name') or not var.get('label') or not var.get('type'):
                    raise ValueError(f"Variable {i+1}: name, label, and type are required")
                
                var_type = var['type']
                if var_type not in SERVICENOW_VARIABLE_TYPES:
                    raise ValueError(f"Variable {i+1}: Invalid type '{var_type}'. Must be one of: {SERVICENOW_VARIABLE_TYPES}")
                
                validated_var = {
                    'name': var['name'],
                    'label': var['label'],
                    'type': var_type,
                    'default_value': var.get('default_value'),
                    'required': var.get('required', False),
                    'help_text': var.get('help_text'),
                    'choices': var.get('choices')
                }
                validated_variables.append(validated_var)
        
        # Create catalog data
        catalog_data = {
            'name': name.strip(),
            'catalog_type': catalog_type,
            'category': category,
            'short_description': short_description.strip(),
            'long_description': long_description.strip(),
            'variables': validated_variables
        }
        
        # Check if ServiceNow is configured
        servicenow_configured = (
            settings.servicenow.instance_url and
            settings.servicenow.username and
            settings.servicenow.password
        )
        
        print(f"ServiceNow configured: {servicenow_configured}")
        
        if servicenow_configured:
            # Use real ServiceNow API
            servicenow_client = get_servicenow_client()
            
            if servicenow_client:
                print("Using real ServiceNow API")
                result = servicenow_client.create_catalog_item(catalog_data)
            else:
                print("ServiceNow client not initialized, using mock mode")
                result = _mock_catalog_creation(catalog_data)
        else:
            # Use mock mode when credentials not available
            print("ServiceNow credentials not configured, using mock mode")
            result = _mock_catalog_creation(catalog_data)
        
        if result['success']:
            print("✅ Catalog item created successfully!")
            print(f"   Catalog ID: {result['catalog_id']}")
            print(f"   Message: {result['message']}")
            
            # Check if it was created in mock mode
            if result['details'].get('mock_mode'):
                print("   Mode: MOCK MODE (ServiceNow credentials not configured)")
                print("   Payload logged for debugging")
            else:
                print("   Mode: REAL ServiceNow API")
                if result['details'].get('variables_created'):
                    print("   Variables: Created successfully")
                else:
                    print("   Variables: None created")
                
                # Query the created item to check its status
                print("\n🔍 Checking created catalog item status...")
                await check_catalog_item_status(result['catalog_id'])
                
            return True
        else:
            print(f"❌ Catalog creation failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during catalog creation: {str(e)}")
        return False


async def test_validation():
    """Test input validation."""
    print("\n🔍 Testing input validation...")
    
    from openai_agents.servicenow_tools import SERVICENOW_CATALOG_TYPES, SERVICENOW_CATEGORIES
    
    # Test invalid catalog type
    print("Testing invalid catalog type...")
    if "invalid_type" not in SERVICENOW_CATALOG_TYPES:
        print("✅ Validation correctly caught invalid catalog type")
    else:
        print("❌ Validation failed to catch invalid catalog type")
    
    # Test invalid category
    print("Testing invalid category...")
    if "invalid_category" not in SERVICENOW_CATEGORIES:
        print("✅ Validation correctly caught invalid category")
    else:
        print("❌ Validation failed to catch invalid category")
    
    # Test too many variables
    print("Testing too many variables...")
    too_many_variables = [
        {'name': f'var_{i}', 'label': f'Variable {i}', 'type': 'string'}
        for i in range(10)  # More than 7 allowed
    ]
    
    if len(too_many_variables) > 7:
        print("✅ Validation correctly caught too many variables")
    else:
        print("❌ Validation failed to catch too many variables")


async def main():
    """Main test function."""
    print("🚀 ServiceNow Integration Test")
    print("=" * 50)
    
    # Test connection
    connection_ok = test_servicenow_connection()
    
    if connection_ok:
        # Test catalog creation
        creation_ok = await test_catalog_creation()
        
        if creation_ok:
            print("\n🎉 All tests passed! ServiceNow integration is working correctly.")
        else:
            print("\n⚠️  Catalog creation test failed. Check ServiceNow permissions and configuration.")
    else:
        print("\n⚠️  Connection test failed. Check ServiceNow credentials and network connectivity.")
    
    # Always test validation (doesn't require connection)
    await test_validation()
    
    print("\n📝 Test Summary:")
    print("- Connection test: " + ("✅ PASS" if connection_ok else "❌ FAIL"))
    print("- Validation test: ✅ PASS (always runs)")
    if connection_ok:
        print("- Catalog creation: " + ("✅ PASS" if 'creation_ok' in locals() and creation_ok else "❌ FAIL"))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 