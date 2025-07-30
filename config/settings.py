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
            location=self._get_env("AZURE_LOCATION", default="eastus"),
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