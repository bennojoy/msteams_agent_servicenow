#!/usr/bin/env python3
"""
Command-line test script for Teams Agent Bot

This script allows you to test the agent system directly from the command line
without needing Microsoft Teams integration.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai_agents.agent_manager import process_user_message, get_agent_stats, list_active_users, clear_user_session
from utils.logger import get_logger

logger = get_logger(__name__)


def print_banner():
    """Print a welcome banner."""
    print("=" * 60)
    print("🤖 TEAMS AGENT BOT - COMMAND LINE TESTER")
    print("=" * 60)
    print("This script simulates Microsoft Teams input for testing agents.")
    print("Type 'help' for available commands.")
    print("Type 'quit' or 'exit' to stop.")
    print("=" * 60)


def print_help():
    """Print help information."""
    print("\n📋 AVAILABLE COMMANDS:")
    print("  help                    - Show this help message")
    print("  quit, exit              - Exit the test script")
    print("  stats                   - Show agent statistics")
    print("  users                   - List active users")
    print("  clear <user_id>         - Clear a user's session")
    print("  <any message>           - Send a message to the agent system")
    print("\n💡 EXAMPLE MESSAGES:")
    print("  'Hello, how can you help me?'")
    print("  'I need to create a new catalog item'")
    print("  'Can you help me add variables to a catalog?'")
    print("  'What VMs do I have running?'")
    print("  'Create a new VM for me'")
    print()


async def test_message(user_id: str, user_name: str, message: str):
    """Test a message with the agent system."""
    print(f"\n👤 User: {user_name} ({user_id})")
    print(f"💬 Message: {message}")
    print("-" * 60)
    
    try:
        # Process the message
        response = await process_user_message(
            user_id=user_id,
            room_id="cli_test",
            message=message,
            user_name=user_name
        )
        
        print(f"🤖 Response: {response}")
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("-" * 60)


async def show_stats():
    """Show agent statistics."""
    try:
        stats = get_agent_stats()
        print("\n📊 AGENT STATISTICS:")
        print("-" * 30)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("-" * 30)
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")


async def show_users():
    """Show active users."""
    try:
        users = list_active_users()
        print("\n👥 ACTIVE USERS:")
        print("-" * 30)
        if users:
            for user_id, agent_name in users.items():
                print(f"  {user_id}: {agent_name}")
        else:
            print("  No active users")
        print("-" * 30)
    except Exception as e:
        print(f"❌ Error getting users: {str(e)}")


async def clear_user(user_id: str):
    """Clear a user's session."""
    try:
        clear_user_session(user_id)
        print(f"✅ Cleared session for user: {user_id}")
    except Exception as e:
        print(f"❌ Error clearing user session: {str(e)}")


async def main():
    """Main test loop."""
    print_banner()
    
    # Default test user
    test_user_id = "cli_test_user_001"
    test_user_name = "CLI Test User"
    
    print(f"🧪 Using test user: {test_user_name} ({test_user_id})")
    print("💡 You can change the user by modifying the script variables.")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("💬 Enter message or command: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif user_input.lower() == 'stats':
                await show_stats()
                continue
            elif user_input.lower() == 'users':
                await show_users()
                continue
            elif user_input.lower().startswith('clear '):
                user_id_to_clear = user_input[6:].strip()
                if user_id_to_clear:
                    await clear_user(user_id_to_clear)
                else:
                    print("❌ Please provide a user ID to clear")
                continue
            
            # Process as a message
            await test_message(test_user_id, test_user_name, user_input)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    # Check if environment is set up
    try:
        from config.settings import settings
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        print("💡 Make sure you have a .env file with proper settings")
        sys.exit(1)
    
    # Run the test
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1) 