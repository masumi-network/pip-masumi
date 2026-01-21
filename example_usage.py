#!/usr/bin/env python3
"""
Example Masumi Agent - A runnable agent that can be used locally and deployed.

This example shows how to create a MIP-003 compliant agent using the simplified masumi.run() approach.
The agent processes text input and returns processed results.

To run:
    # API mode (default) - runs as FastAPI server
    masumi run example_usage.py
    # Or: python example_usage.py

    # Standalone mode - executes job directly without API
    masumi run example_usage.py --standalone
    # Or: masumi run example_usage.py --standalone --input '{"text": "Hello", "operation": "uppercase"}'

Required environment variables for API mode:
    - AGENT_IDENTIFIER: Your agent ID from admin interface (OPTIONAL for starting the API, but REQUIRED after registration for the API to work completely)
    - PAYMENT_API_KEY: Your payment API key (REQUIRED for API)
    - SELLER_VKEY: Your seller wallet verification key (REQUIRED for API)
    - PAYMENT_SERVICE_URL: Payment service URL (optional, defaults to production)
    - NETWORK: Network to use - 'Preprod' or 'Mainnet' (optional, defaults to 'Preprod')
"""

import os
from masumi import run

# Note: .env files are automatically loaded by masumi.run() from the current directory

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Agent Logic - This is where you implement your actual agent functionality
# ─────────────────────────────────────────────────────────────────────────────

async def process_job(identifier_from_purchaser: str, input_data: dict):
    """
    Process a job - can be run locally or via Masumi API.
    
    When used with Masumi API: This function runs automatically after payment is confirmed.
    The payment creation, monitoring, and completion are all handled automatically.
    
    When run locally: This function can be executed directly without any masumi setup.
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser (can be any string for local testing)
        input_data: Input data matching your input schema
    
    Returns:
        Result of the processing (string, dict, or any serializable type)
    """
    logger.info(f"Processing job for purchaser: {identifier_from_purchaser}")
    logger.info(f"Input data: {input_data}")
    
    # Extract input
    text = input_data.get("text", "")
    operation = input_data.get("operation", "uppercase")
    
    # Process based on operation type
    if operation == "uppercase":
        result = text.upper()
    elif operation == "lowercase":
        result = text.lower()
    elif operation == "reverse":
        result = text[::-1]
    elif operation == "word_count":
        words = text.split()
        result = f"Word count: {len(words)}"
    else:
        result = f"Processed: {text}"
    
    logger.info(f"Processing complete. Result: {result[:100]}...")  # Log first 100 chars
    
    # Return result - can be string, dict, or any serializable type
    return {
        "status": "completed",
        "result": result,
        "operation": operation,
        "input_length": len(text)
    }


# ─────────────────────────────────────────────────────────────────────────────
# Input Schema - Define what input fields your agent expects
# ─────────────────────────────────────────────────────────────────────────────

# RECOMMENDED: Static schema (dict) - most agents use fixed input schemas
INPUT_SCHEMA = {
    "input_data": [
        {
            "id": "text",
            "type": "string",
            "name": "Text to Process"
        },
        {
            "id": "operation",
            "type": "option",
            "name": "Operation"
        }
    ]
}

# OPTIONAL: Dynamic schema function (only if you need schema to change based on context)
# Uncomment and use this instead of INPUT_SCHEMA if you need dynamic behavior:
# def get_input_schema():
#     """
#     Dynamic schema function - use only if schema needs to change based on context
#     (e.g., user permissions, configuration, time, etc.)
#     """
#     # Example: could vary based on user subscription, time of day, etc.
#     return INPUT_SCHEMA


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point - Simplified approach using masumi.run()
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Config and identifiers loaded from environment variables automatically
    # Default mode is API - use --standalone flag to run standalone
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
        # config, agent_identifier, network loaded from env vars automatically
        # For dynamic schema, use: input_schema_handler=get_input_schema
    )
