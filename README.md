# Teams Agent Bot

A sophisticated Microsoft Teams bot that integrates with OpenAI agents to provide intelligent assistance, featuring a concierge agent, specialized Azure VM management capabilities, and comprehensive ServiceNow catalog and variable creation functionality.

## 🚀 Features

- **Intelligent Agent Routing**: Automatically routes user requests to appropriate agents
- **Concierge Agent**: Handles general questions and user assistance
- **Azure VM Subagent**: Specialized for Azure virtual machine management
- **ServiceNow Catalog Creation Agent**: Creates and publishes ServiceNow catalog items with intelligent category suggestions
- **ServiceNow Variables Agent**: Adds variables/fields to catalog items with smart type detection and suggestions
- **Conversation History**: Maintains context-aware conversations per user
- **Structured Logging**: Comprehensive logging for debugging and monitoring
- **Health Monitoring**: Built-in health check endpoints
- **Configurable**: Extensive configuration options via environment variables

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Microsoft     │───▶│  Teams Bot       │───▶│  OpenAI Agents  │
│   Teams         │    │  (app.py)        │    │  (Concierge +   │
│                  │    │                  │    │   Azure VM +    │
│                  │    │                  │    │   ServiceNow)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Message History │
                       │  & Context Mgmt  │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  ServiceNow API  │
                       │  Integration     │
                       └──────────────────┘
```

### Core Components

1. **Teams Bot Interface** (`app.py`): Handles Teams integration and message routing
2. **Agent Manager** (`agents/agent_manager.py`): Orchestrates agent interactions
3. **Message History** (`storage/message_history.py`): Manages conversation context
4. **OpenAI Client** (`utils/openai_client.py`): OpenAI API integration
5. **ServiceNow Integration** (`openai_agents/servicenow_api.py`): ServiceNow REST API client
6. **Configuration** (`config/settings.py`): Centralized configuration management
7. **Logging** (`utils/logger.py`): Structured logging system

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Microsoft Teams Bot registration
- Azure subscription (for VM operations)
- ServiceNow instance with API access
- OpenAI agents (concierge, Azure VM, and ServiceNow agents)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd teams_agent_bot
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

## ⚙️ Configuration

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
CONCIERGE_AGENT_ID=your_concierge_agent_id_here
AZURE_VM_AGENT_ID=your_azure_vm_agent_id_here

# Microsoft Teams Bot Configuration
MICROSOFT_APP_ID=your_teams_bot_app_id_here
MICROSOFT_APP_PASSWORD=your_teams_bot_password_here

# Azure Configuration
AZURE_SUBSCRIPTION_ID=your_azure_subscription_id_here
AZURE_RESOURCE_GROUP=your_azure_resource_group_here

# ServiceNow Configuration
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_servicenow_username
SERVICENOW_PASSWORD=your_servicenow_password_or_api_key
```

### Optional Configuration

```bash
# Bot Server
BOT_PORT=3978
BOT_HOST=0.0.0.0

# Agent Settings
MAX_HISTORY_MESSAGES=50
HISTORY_RETENTION_DAYS=30

# Logging
LOG_LEVEL=INFO
LOG_ENABLE_CONSOLE=true
LOG_ENABLE_FILE=false
```

## 🚀 Running the Bot

1. **Start the bot server**:
   ```bash
   python app.py
   ```

2. **Verify the bot is running**:
   ```bash
   curl http://localhost:3978/health
   ```

3. **Configure Teams integration**:
   - Set the messaging endpoint to: `https://your-domain.com/api/messages`
   - Configure authentication in Azure Bot Service

## 📝 Usage Examples

### General Questions (Concierge Agent)
```
User: "Hello, how can you help me?"
Bot: "Hello! I'm your AI assistant. I can help you with general questions, 
     provide information, and assist with Azure VM management. What would you like to know?"
```

### Azure VM Operations (Azure VM Agent)
```
User: "Can you create a new VM for me?"
Bot: "I'd be happy to help you create a new Azure VM! I'll need some information:
     - What would you like to name the VM?
     - What operating system would you prefer?
     - Any specific requirements for the VM size?"
```

### ServiceNow Catalog Creation (ServiceNow Catalog Agent)
```
User: "I need to create a catalog item for requesting new laptops"
Bot: "I can see you want to create a catalog item for requesting new laptops. Based on your description, I suggest:
     Name: New Laptop Request
     Long Description: Request a new laptop for employees. This catalog item allows users to submit requests for new laptop computers, including specifications and delivery preferences. The request will be reviewed by IT and processed according to company policies.
     
     Would you like to use these suggestions, or would you like to modify either the name or long description?"
```

### ServiceNow Variable Creation (ServiceNow Variables Agent)
```
User: "I want to add variables to my catalog"
Bot: "I can see you just created a catalog item. Let me get the details for adding variables.
     Based on your catalog 'New Laptop Request', I suggest these variables:
     - Employee Name (String/Single line text field for who needs the laptop)
     - Department (Select Box with IT, HR, Finance, etc.)
     - Priority Level (Multiple Choice with Critical, High, Medium, Low)
     - Laptop Model Preference (String/Single line text field for specific requirements)
     - Delivery Date (Date field for when needed)
     
     Would you like me to create these suggested variables, or would you prefer to create custom ones?"
```

### Conversation Context
```
User: "What VMs do I have running?"
Bot: "Let me check your Azure VMs for you..."
[Bot lists VMs]

User: "Stop the first one"
Bot: "I'll stop the VM named 'web-server-01' for you. This will shut down the VM 
     but preserve all data. Would you like me to proceed?"
```

## 🔧 Development

### Project Structure
```
teams_agent_bot/
├── app.py                          # Main application
├── agents/
│   ├── agent_manager.py            # Agent orchestration
│   └── __init__.py
├── config/
│   ├── settings.py                 # Configuration management
│   └── __init__.py
├── storage/
│   ├── message_history.py          # Conversation storage
│   └── __init__.py
├── utils/
│   ├── logger.py                   # Logging system
│   ├── openai_client.py            # OpenAI integration
│   └── __init__.py
├── openai_agents/
│   ├── servicenow_api.py           # ServiceNow REST API client
│   ├── servicenow_catalog_tools.py # Catalog creation tools
│   ├── servicenow_variables_tools.py # Variable creation tools
│   ├── instructions/
│   │   ├── servicenow_catalog_creation_agent.py # Catalog agent instructions
│   │   └── servicenow_variables_agent.py # Variables agent instructions
│   └── __init__.py
├── test_cli.py                     # Command-line testing script
├── requirements.txt                # Dependencies
├── env.example                     # Environment template
└── README.md                       # This file
```

### Adding New Agents

1. **Create agent in OpenAI**
2. **Add agent ID to configuration**
3. **Update agent selection logic in `agent_manager.py`**
4. **Add agent-specific instructions**

### ServiceNow Integration Features

#### Catalog Creation Agent
- **Smart Description Detection**: Automatically detects short descriptions from user's initial message
- **Intelligent Category Suggestions**: Uses LLM to suggest relevant categories based on catalog description
- **Automatic Publishing**: Creates and publishes catalog items in one step
- **Enhanced Response Formatting**: Provides detailed summaries with catalog IDs and status
- **User Confirmation**: Always asks for user confirmation before proceeding

#### Variables Agent
- **Context Awareness**: Automatically detects catalog creation context from conversation history
- **Smart Variable Suggestions**: Analyzes catalog purpose and suggests relevant variables
- **Intelligent Type Detection**: Automatically suggests variable types based on question text
- **Automatic Name Generation**: Generates internal variable names from user-friendly labels
- **Choice Suggestions**: Suggests appropriate choices for Select Box and Multiple Choice variables

#### API Integration
- **Comprehensive Logging**: Logs all API calls, payloads, and responses for debugging
- **Error Handling**: Detailed error messages and recovery suggestions
- **Field Mapping**: Correct ServiceNow field mappings for all data types
- **Search Capabilities**: Smart catalog lookup and filtering

### Logging

The bot uses structured logging with multiple levels:

```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing message", user_id="123", message_length=50)
logger.error("Error occurred", error_type="ConnectionError")
```

### Health Monitoring

Check bot health:
```bash
curl http://localhost:3978/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "agent_stats": {
    "total_conversations": 5,
    "total_messages": 25,
    "active_users": 3,
    "agent_usage": {
      "concierge": 10,
      "azure_vm": 5,
      "servicenow_catalog": 3,
      "servicenow_variables": 2
    }
  }
}
```

### Testing

Use the command-line testing script to test agents without Teams integration:

```bash
python test_cli.py
```

Available commands:
- `help` - Show available commands
- `stats` - Show agent statistics
- `users` - List active users
- `clear <user_id>` - Clear a user's session
- Any other text - Send as a message to the agent system

## 🐛 Troubleshooting

### Common Issues

1. **Configuration Errors**:
   - Verify all required environment variables are set
   - Check OpenAI API key validity
   - Ensure Teams bot credentials are correct
   - Verify ServiceNow instance URL and credentials

2. **OpenAI Agent Issues**:
   - Verify agent IDs exist in your OpenAI account
   - Check agent permissions and tools
   - Ensure API rate limits aren't exceeded

3. **Teams Integration**:
   - Verify messaging endpoint URL is accessible
   - Check bot authentication in Azure Bot Service
   - Ensure proper CORS configuration

4. **ServiceNow Integration**:
   - Verify ServiceNow instance URL is accessible
   - Check API credentials and permissions
   - Ensure catalog and variable creation permissions
   - Review API logs for detailed error information

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python app.py
```

### Log Files

Enable file logging:
```bash
LOG_ENABLE_FILE=true
LOG_FILE_PATH=./logs/bot.log
```

## 🔒 Security

- **Environment Variables**: Never commit `.env` files to version control
- **API Keys**: Use secure methods to manage API keys
- **Authentication**: Implement proper Teams bot authentication
- **Input Validation**: All user inputs are validated and sanitized

## 📈 Monitoring

### Metrics Available

- Total conversations
- Messages per user
- Agent usage statistics (Concierge, Azure VM, ServiceNow Catalog, ServiceNow Variables)
- Error rates
- Response times
- ServiceNow API call statistics

### Health Checks

- OpenAI API connectivity
- Teams bot authentication
- Message history storage
- Agent availability
- ServiceNow API connectivity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error details
- Open an issue on GitHub

## 🔄 Version History

- **v1.0.0**: Initial release with concierge and Azure VM agents
- **v1.1.0**: Added structured logging and health monitoring
- **v1.2.0**: Enhanced conversation history and context management
- **v1.3.0**: Added comprehensive ServiceNow integration with catalog and variable creation agents
  - Smart description detection from user messages
  - Intelligent category suggestions using LLM
  - Automatic catalog publishing
  - Context-aware variable creation
  - Comprehensive API logging and error handling
  - Command-line testing script 