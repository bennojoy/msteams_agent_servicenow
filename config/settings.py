"""
Configuration settings for Teams Agent Bot.

This module handles all configuration management including environment variables,
default values, and validation. It provides a centralized way to manage all
bot settings and ensures proper configuration validation.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class OpenAIConfig:
    """OpenAI API configuration settings."""
    api_key: str
    organization: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3


@dataclass
class BotConfig:
    """Microsoft Teams Bot configuration settings."""
    app_id: str
    app_password: str
    port: int = 3978
    host: str = "0.0.0.0"


@dataclass
class AgentConfig:
    """Agent-specific configuration settings."""
    concierge_agent_id: str
    azure_vm_agent_id: str
    max_history_messages: int = 120
    history_retention_days: int = 30
    conversation_timeout_minutes: int = 30


@dataclass
class AzureConfig:
    """Azure-specific configuration settings."""
    subscription_id: str
    resource_group: str
    location: str = "eastus"
    # Authentication (optional - will use Azure CLI if not provided)
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None


@dataclass
class ServiceNowConfig:
    """ServiceNow-specific configuration settings."""
    instance_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    # Authentication method: 'basic' (username/password) or 'oauth' (client_id/secret)
    auth_method: str = "basic"


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    enable_console: bool = True
    enable_file: bool = False


@dataclass
class VariableSetConfig:
    """ServiceNow Variable Set configuration settings."""
    # Default variable set IDs for different catalog types
    hardware_request_set_id: str = "e5db6ac4c303665081ef1275e4013132"
    software_request_set_id: str = "e5db6ac4c303665081ef1275e4013132"
    access_request_set_id: str = "e5db6ac4c303665081ef1275e4013132"
    general_request_set_id: str = "e5db6ac4c303665081ef1275e4013132"
    
    def get_variable_set_id_for_catalog_type(self, catalog_type: str) -> str:
        """Get the appropriate variable set ID based on catalog type/purpose."""
        catalog_type_lower = catalog_type.lower()
        
        if any(keyword in catalog_type_lower for keyword in ['hardware', 'laptop', 'desktop', 'equipment', 'device']):
            return self.hardware_request_set_id
        elif any(keyword in catalog_type_lower for keyword in ['software', 'application', 'license']):
            return self.software_request_set_id
        elif any(keyword in catalog_type_lower for keyword in ['access', 'permission', 'role', 'group']):
            return self.access_request_set_id
        else:
            return self.general_request_set_id


@dataclass
class WaitToolsConfig:
    """Configuration for tools that should show wait messages and are available to agents."""
    # Tools that trigger wait messages and are available to each agent
    # Uncomment the tools you want to enable for each agent
    agent_wait_tools: Dict[str, list[str]] = None
    
    def __post_init__(self):
        if self.agent_wait_tools is None:
            self.agent_wait_tools = {
                "ServiceNowCatalogCreationAgent": [
                    # Create/Modify Tools (show wait messages)
                    "create_catalog_item",                    # Create new catalog item
                    "create_and_publish_catalog_item",        # Create and publish catalog item
                    "publish_catalog_item",                   # Publish existing catalog item
                    #"create_string_variable",                 # Add string variable to catalog
                    #"create_boolean_variable",                # Add boolean variable to catalog
                    #"create_choice_variable",                 # Add choice/dropdown variable to catalog
                    #"create_multiple_choice_variable",        # Add multiple choice variable to catalog
                    #"create_date_variable",                   # Add date variable to catalog
                    
                    # Get/Read Tools (no wait messages, but controlled access)
                    # "search_catalog_items",                # Search for catalog items by name/number
                    # "list_catalog_items",                  # List catalog items with optional category filter
                    # "get_catalog_details",                 # Get detailed info about a specific catalog item
                     "get_servicenow_categories",           # Get available ServiceNow categories
                    # "get_servicenow_catalog_types",        # Get available ServiceNow catalog types
                ],
                "AzureVMAgent": [
                    # Create/Modify Tools (show wait messages)
                    #"create_vm",                             # Create new virtual machine
                    #"start_vm",                              # Start a virtual machine
                    #"stop_vm",                               # Stop a virtual machine
                    #"delete_vm",                             # Delete a virtual machine
                    
                    # Get/Read Tools (no wait messages, but controlled access)
                    # "list_vms",                           # List all VMs in the resource group
                    # "get_vm_status",                      # Get detailed status of a specific VM
                ],
                "ServiceNowVariablesAgent": [
                    # Create/Modify Tools (show wait messages)
                    #"create_string_variable",                 # Add string variable to catalog
                    #"create_boolean_variable",                # Add boolean variable to catalog
                    #"create_choice_variable",                 # Add choice/dropdown variable to catalog
                    #"create_multiple_choice_variable",        # Add multiple choice variable to catalog
                    #"create_date_variable",                   # Add date variable to catalog
                    "add_multiple_variables",                 # Create multiple variables at once with proper ordering
                    #"publish_catalog_item",                   # Publish catalog item after adding variables
                    
                    # Get/Read Tools (no wait messages, but controlled access)
                    # "search_catalog_items",                # Search for catalog items by name/number
                    # "list_catalog_items",                  # List catalog items with optional category filter
                    # "get_catalog_details",                 # Get detailed info about a specific catalog item
                    # "get_servicenow_variable_types",       # Get available ServiceNow variable types
                ],
                "ConciergeAgent": [
                    # Get/Read Tools (no wait messages, but controlled access)
                    # "search_catalog_items",                # Search for catalog items by name/number
                    # "list_catalog_items",                  # List catalog items with optional category filter
                    # "get_catalog_details",                 # Get detailed info about a specific catalog item
                    # "get_servicenow_categories",           # Get available ServiceNow categories
                    # "get_servicenow_catalog_types",        # Get available ServiceNow catalog types
                    # "get_servicenow_variable_types",       # Get available ServiceNow variable types
                    # "list_vms",                           # List all VMs in the resource group
                    # "get_vm_status",                      # Get detailed status of a specific VM
                ]
            }
    
    def get_wait_tools_for_agent(self, agent_name: str) -> list[str]:
        """Get the list of wait tools for a specific agent."""
        return self.agent_wait_tools.get(agent_name, [])
    
    def is_wait_tool(self, agent_name: str, tool_name: str) -> bool:
        """Check if a tool should trigger a wait message for a specific agent."""
        wait_tools = self.get_wait_tools_for_agent(agent_name)
        return tool_name in wait_tools
    
    def add_wait_tool(self, agent_name: str, tool_name: str) -> None:
        """Add a tool to the wait list for a specific agent."""
        if agent_name not in self.agent_wait_tools:
            self.agent_wait_tools[agent_name] = []
        if tool_name not in self.agent_wait_tools[agent_name]:
            self.agent_wait_tools[agent_name].append(tool_name)
    
    def remove_wait_tool(self, agent_name: str, tool_name: str) -> None:
        """Remove a tool from the wait list for a specific agent."""
        if agent_name in self.agent_wait_tools and tool_name in self.agent_wait_tools[agent_name]:
            self.agent_wait_tools[agent_name].remove(tool_name)





class Settings:
    """
    Main settings class that aggregates all configuration.
    
    This class provides a single point of access to all configuration
    settings and handles validation of required environment variables.
    """
    
    def __init__(self):
        """Initialize settings with environment variables."""
        self._validate_required_env_vars()
        
        # OpenAI Configuration
        self.openai = OpenAIConfig(
            api_key=self._get_env("OPENAI_API_KEY"),
            organization=self._get_env("OPENAI_ORG_ID", required=False),
            base_url=self._get_env("OPENAI_BASE_URL", required=False),
            timeout=int(self._get_env("OPENAI_TIMEOUT", default="60")),
            max_retries=int(self._get_env("OPENAI_MAX_RETRIES", default="3"))
        )
        
        # Bot Configuration
        self.bot = BotConfig(
            app_id=self._get_env("MICROSOFT_APP_ID"),
            app_password=self._get_env("MICROSOFT_APP_PASSWORD"),
            port=int(self._get_env("BOT_PORT", default="3978")),
            host=self._get_env("BOT_HOST", default="0.0.0.0")
        )
        
        # Agent Configuration
        self.agent = AgentConfig(
            concierge_agent_id=self._get_env("CONCIERGE_AGENT_ID", default="concierge_agent"),
            azure_vm_agent_id=self._get_env("AZURE_VM_AGENT_ID", default="azure_vm_agent"),
            max_history_messages=int(self._get_env("MAX_HISTORY_MESSAGES", default="120")),
            history_retention_days=int(self._get_env("HISTORY_RETENTION_DAYS", default="30")),
            conversation_timeout_minutes=int(self._get_env("CONVERSATION_TIMEOUT_MINUTES", default="30"))
        )
        
        # Azure Configuration
        self.azure = AzureConfig(
            subscription_id=self._get_env("AZURE_SUBSCRIPTION_ID", default="test_subscription"),
            resource_group=self._get_env("AZURE_RESOURCE_GROUP", default="test_resource_group"),
            location=self._get_env("AZURE_LOCATION", default="australiaeast"),
            client_id=self._get_env("AZURE_CLIENT_ID", required=False),
            client_secret=self._get_env("AZURE_CLIENT_SECRET", required=False),
            tenant_id=self._get_env("AZURE_TENANT_ID", required=False)
        )
        
        # ServiceNow Configuration
        self.servicenow = ServiceNowConfig(
            instance_url=self._get_env("SERVICENOW_INSTANCE_URL", required=False),
            username=self._get_env("SERVICENOW_USERNAME", required=False),
            password=self._get_env("SERVICENOW_PASSWORD", required=False),
            client_id=self._get_env("SERVICENOW_CLIENT_ID", required=False),
            client_secret=self._get_env("SERVICENOW_CLIENT_SECRET", required=False),
            auth_method=self._get_env("SERVICENOW_AUTH_METHOD", default="basic")
        )
        
        # Logging Configuration
        self.logging = LoggingConfig(
            level=self._get_env("LOG_LEVEL", default="INFO"),
            format=self._get_env("LOG_FORMAT", default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=self._get_env("LOG_FILE_PATH", required=False),
            enable_console=self._get_env("LOG_ENABLE_CONSOLE", default="true").lower() == "true",
            enable_file=self._get_env("LOG_ENABLE_FILE", default="false").lower() == "true"
        )
        
        # Wait Tools Configuration
        self.wait_tools = WaitToolsConfig()
        
        # Allow environment variable override for wait tools (optional)
        wait_tools_env = self._get_env("WAIT_TOOLS_CONFIG", required=False)
        if wait_tools_env:
            try:
                import json
                custom_wait_tools = json.loads(wait_tools_env)
                self.wait_tools.agent_wait_tools.update(custom_wait_tools)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid WAIT_TOOLS_CONFIG environment variable: {e}")
        
        # Variable Set Configuration
        self.variable_sets = VariableSetConfig(
            hardware_request_set_id=self._get_env("HARDWARE_REQUEST_SET_ID", default="e5db6ac4c303665081ef1275e4013132"),
            software_request_set_id=self._get_env("SOFTWARE_REQUEST_SET_ID", default="e5db6ac4c303665081ef1275e4013132"),
            access_request_set_id=self._get_env("ACCESS_REQUEST_SET_ID", default="e5db6ac4c303665081ef1275e4013132"),
            general_request_set_id=self._get_env("GENERAL_REQUEST_SET_ID", default="e5db6ac4c303665081ef1275e4013132")
        )
        

    
    def _get_env(self, key: str, default: Optional[str] = None, required: bool = True) -> str:
        """
        Get environment variable with validation.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether the variable is required
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required variable is missing
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value
    
    def _validate_required_env_vars(self):
        """Validate that all required environment variables are set."""
        required_vars = [
            "OPENAI_API_KEY",
            "MICROSOFT_APP_ID", 
            "MICROSOFT_APP_PASSWORD"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for logging/debugging."""
        return {
            "openai": {
                "api_key": "***" if self.openai.api_key else None,
                "organization": self.openai.organization,
                "base_url": self.openai.base_url,
                "timeout": self.openai.timeout,
                "max_retries": self.openai.max_retries
            },
            "bot": {
                "app_id": self.bot.app_id,
                "port": self.bot.port,
                "host": self.bot.host
            },
            "agent": {
                "max_history_messages": self.agent.max_history_messages,
                "history_retention_days": self.agent.history_retention_days,
                "conversation_timeout_minutes": self.agent.conversation_timeout_minutes
            },
            "azure": {
                "subscription_id": self.azure.subscription_id,
                "resource_group": self.azure.resource_group,
                "location": self.azure.location,
                "client_id": "***" if self.azure.client_id else None,
                "tenant_id": self.azure.tenant_id
            },
            "logging": {
                "level": self.logging.level,
                "enable_console": self.logging.enable_console,
                "enable_file": self.logging.enable_file,
                "file_path": self.logging.file_path
            }
        }


# Global settings instance
settings = Settings() 