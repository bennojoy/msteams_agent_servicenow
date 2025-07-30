"""
Teams Agent Bot - Main Application

This is the main entry point for the Teams Agent Bot that integrates
with Microsoft Teams and OpenAI agents to provide intelligent assistance.
"""

import os
import json
import aiohttp
from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
)
from botbuilder.schema import Activity

# Import our custom modules
from config.settings import settings
from utils.logger import get_logger, log_function_call, log_function_result, log_error_with_context
from openai_agents.agent_manager import process_user_message

# Initialize logger
logger = get_logger(__name__)

# Initialize bot adapter
adapter_settings = BotFrameworkAdapterSettings(settings.bot.app_id, settings.bot.app_password)
adapter = BotFrameworkAdapter(adapter_settings)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    """Handle bot framework errors with proper logging."""
    log_error_with_context(logger, error, {
        "operation": "bot_framework_error",
        "user_id": context.activity.from_property.id if context.activity.from_property else "unknown",
        "activity_type": context.activity.type
    })
    await context.send_activity("I apologize, but I encountered an error. Please try again.")

adapter.on_turn_error = on_error

# Main message handler
async def messages(req: web.Request) -> web.Response:
    """
    Handle incoming messages from Teams.
    
    This function processes all incoming messages from Microsoft Teams,
    extracts user information, and routes them to the appropriate agent
    for processing.
    """
    log_function_call(logger, "messages_handler")
    
    try:
        # Debug: Log request details
        logger.info("=== INCOMING REQUEST DEBUG ===")
        logger.info(f"Request headers: {dict(req.headers)}")
        logger.info(f"Request method: {req.method}")
        logger.info(f"Request URL: {req.url}")
        
        body = await req.json()
        logger.info(f"Request body: {json.dumps(body, indent=2)}")
        
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")
        
        # Debug: Log authorization header
        logger.info(f"Authorization header: {auth_header[:50] if auth_header else 'NOT PROVIDED'}...")
        logger.info(f"Activity type: {activity.type}")
        logger.info(f"Activity text: {activity.text}")
        logger.info(f"Activity from: {activity.from_property}")
        logger.info(f"Activity channel: {activity.channel_id}")
        logger.info("=== END REQUEST DEBUG ===")
        
        async def call_agent_logic(context: TurnContext):
            """Process the incoming message with our agent system."""
            if context.activity.type == "message":
                # Extract user information
                user_text = context.activity.text
                user_id = context.activity.from_property.id
                user_name = context.activity.from_property.name
                user_email = getattr(context.activity.from_property, 'aad_object_id', 'N/A')
                logger.info(f" Context: {context.activity.additional_properties}")

                # Log incoming message
                logger.info("Received message from Teams", 
                           user_id=user_id,
                           user_name=user_name,
                           user_email=user_email,
                           message_length=len(user_text))
                
                try:
                    # Process message with agent manager
                    response = await process_user_message(
                        user_id=user_id,
                        room_id="default",
                        message=user_text,
                        user_name=user_name
                    )
                    
                    # Debug: Log response details
                    logger.info("=== RESPONSE DEBUG ===")
                    logger.info(f"Agent response: {response}")
                    logger.info(f"Response length: {len(response)}")
                    logger.info(f"Context activity: {context.activity}")
                    logger.info(f"Context service URL: {context.activity.service_url}")
                    logger.info(f"Context channel: {context.activity.channel_id}")
                    
                    # Send response back to Teams
                    logger.info("Attempting to send response...")
                    await context.send_activity(response)
                    logger.info("✅ Response sent successfully!")
                    logger.info("=== END RESPONSE DEBUG ===")
                    
                    logger.info("Message processed successfully", 
                               user_id=user_id,
                               response_length=len(response))
                    
                except Exception as e:
                    logger.error("=== ERROR DEBUG ===")
                    logger.error(f"Error type: {type(e).__name__}")
                    logger.error(f"Error message: {str(e)}")
                    logger.error(f"Error details: {e}")
                    logger.error("=== END ERROR DEBUG ===")
                    
                    log_error_with_context(logger, e, {
                        "operation": "process_user_message",
                        "user_id": user_id
                    })
                    
                    # Send error response
                    error_response = "I apologize, but I encountered an error processing your message. Please try again."
                    try:
                        await context.send_activity(error_response)
                        logger.info("✅ Error response sent successfully")
                    except Exception as send_error:
                        logger.error(f"❌ Failed to send error response: {send_error}")
        
        # Process the activity
        await adapter.process_activity(activity, auth_header, call_agent_logic)
        
        log_function_result(logger, "messages_handler", "success")
        return web.Response(status=200)
        
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "messages_handler"})
        return web.Response(status=500, text="Internal server error")

# Create and run web server
app = web.Application()

# Add routes
app.router.add_post("/api/messages", messages)

# Add health check endpoint
async def health_check(req: web.Request) -> web.Response:
    """Health check endpoint for monitoring."""
    try:
        from openai_agents.agent_manager import get_agent_stats
        stats = get_agent_stats()
        
        # Ensure all values are JSON serializable
        def make_json_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            else:
                return obj
        
        serializable_stats = make_json_serializable(stats)
        
        return web.json_response({
            "status": "healthy",
            "timestamp": serializable_stats.get("timestamp"),
            "agent_stats": serializable_stats
        })
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "health_check"})
        return web.json_response({"status": "unhealthy", "error": str(e)}, status=500)

app.router.add_get("/health", health_check)

if __name__ == "__main__":
    logger.info("Starting Teams Agent Bot", 
               port=settings.bot.port,
               host=settings.bot.host,
               log_level=settings.logging.level)
    
    try:
        web.run_app(app, port=settings.bot.port, host=settings.bot.host)
    except Exception as e:
        log_error_with_context(logger, e, {"operation": "start_server"})
        raise

