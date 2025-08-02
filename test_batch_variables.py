#!/usr/bin/env python3
"""
Test script for batch variable creation functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai_agents.servicenow_api import get_servicenow_client
from openai_agents.servicenow_variables_tools import VariableDefinition

def test_batch_variable_creation():
    """Test the batch variable creation functionality."""
    
    # Load environment variables
    load_dotenv()
    
    # Get ServiceNow client
    servicenow = get_servicenow_client()
    if not servicenow:
        print("❌ ServiceNow client not available")
        return False
    
    # Test catalog identifier (you'll need to replace this with a real catalog ID)
    test_catalog_id = "0b16d31ac38f2a1081ef1275e4013166"  # Replace with actual catalog ID
    
    # Test variables using Pydantic models
    test_variables = [
        VariableDefinition(
            type='string',
            name='test_string_var',
            label='Test String Variable',
            required=False,
            help_text='This is a test string variable'
        ),
        VariableDefinition(
            type='boolean',
            name='test_boolean_var',
            label='Test Boolean Variable',
            required=False,
            default_value='false'
        ),
        VariableDefinition(
            type='date',
            name='test_date_var',
            label='Test Date Variable',
            required=False
        ),
        VariableDefinition(
            type='reference',
            name='test_reference_var',
            label='Test Reference Variable',
            reference_table='sys_user',
            reference_qual_condition='active=true',
            required=False
        )
    ]
    
    print(f"🧪 Testing batch variable creation for catalog: {test_catalog_id}")
    print(f"📋 Creating {len(test_variables)} test variables...")
    
    try:
        # Convert Pydantic models to dictionaries for the API call
        variables_dict = [var.model_dump() for var in test_variables]
        
        # Test the batch creation
        result = servicenow.create_multiple_variables(test_catalog_id, variables_dict)
        
        if result.get('success'):
            print(f"✅ Batch creation successful!")
            print(f"📊 Results:")
            print(f"   - Total requested: {result.get('total_requested', 0)}")
            print(f"   - Total created: {result.get('total_created', 0)}")
            print(f"   - Total failed: {result.get('total_failed', 0)}")
            
            if result.get('variables_created'):
                print(f"   - Created variables:")
                for var in result['variables_created']:
                    print(f"     • {var['name']} ({var['type']}) - Order: {var['order']}")
            
            if result.get('variables_failed'):
                print(f"   - Failed variables:")
                for var in result['variables_failed']:
                    print(f"     • {var['name']} ({var['type']}) - Error: {var['error']}")
            
            return True
        else:
            print(f"❌ Batch creation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during batch creation: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting batch variable creation test...")
    success = test_batch_variable_creation()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1) 