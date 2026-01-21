#!/usr/bin/env python3
"""
Examples showing the two different ways to use AgentEndpointHandler.

This demonstrates why we initialize with None and add handlers later.
"""

from masumi import create_masumi_app, MasumiAgentServer, Config

# ============================================================================
# PATTERN 1: Pass handlers during initialization (most common)
# ============================================================================

def pattern1_functional_style():
    """
    Pattern 1: Functional style - pass handlers as arguments.
    
    This is what create_masumi_app() uses internally.
    """
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_key"
    )
    
    async def process_job(identifier: str, input_data: dict):
        return {"result": "done"}
    
    # RECOMMENDED: Static schema (dict) - most agents use this
    INPUT_SCHEMA = {"input_data": [{"id": "text", "type": "string"}]}
    
    # Handlers passed directly as arguments
    app = create_masumi_app(
        config=config,
        agent_identifier="my-agent",
        start_job_handler=process_job,      # Pass function directly
        input_schema_handler=INPUT_SCHEMA    # Pass static schema dict (recommended)
    )
    
    return app


# ============================================================================
# PATTERN 2: Use decorators after creation (alternative style)
# ============================================================================

def pattern2_decorator_style():
    """
    Pattern 2: Decorator style - register handlers after creation.
    
    This is useful when you want to define handlers near where they're used,
    or when handlers depend on other setup that happens after server creation.
    """
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_key"
    )
    
    # Create server first (handlers are None at this point)
    server = MasumiAgentServer(
        config=config,
        agent_identifier="my-agent"
        # Notice: no handlers passed here!
    )
    
    # Now register handlers using decorators
    # The @ decorator syntax calls server.start_job(process_job)
    @server.start_job
    async def process_job(identifier: str, input_data: dict):
        # Handler defined right here, near the decorator
        return {"result": "done"}
    
    # RECOMMENDED: Static schema (dict) - pass directly
    INPUT_SCHEMA = {"input_data": [{"id": "text", "type": "string"}]}
    server.input_schema(INPUT_SCHEMA)  # Register static schema
    
    # OPTIONAL: Dynamic schema (function) - only if schema needs to change
    # @server.input_schema
    # def get_schema():
    #     # Dynamic schema - use only if schema needs to vary based on context
    #     return {"input_data": [{"id": "text", "type": "string"}]}
    
    # Get the FastAPI app after handlers are registered
    app = server.get_app()
    
    return app


# ============================================================================
# PATTERN 3: Mix and match (shows flexibility)
# ============================================================================

def pattern3_mixed_style():
    """
    Pattern 3: Mix both styles - some handlers passed, some added later.
    
    This shows the flexibility of the design!
    """
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_key"
    )
    
    async def process_job(identifier: str, input_data: dict):
        return {"result": "done"}
    
    # Create server with some handlers
    server = MasumiAgentServer(
        config=config,
        agent_identifier="my-agent",
        start_job_handler=process_job  # Pass this one
        # input_schema_handler not passed - will add it later
    )
    
    # Add other handlers later using decorators or direct assignment
    # RECOMMENDED: Static schema (dict)
    INPUT_SCHEMA = {"input_data": [{"id": "text", "type": "string"}]}
    server.input_schema(INPUT_SCHEMA)  # Register static schema
    
    # Or add handlers programmatically
    def custom_status(job_id: str):
        return {"status": "custom"}
    
    server.handler.set_status_handler(custom_status)
    
    # OPTIONAL: Dynamic schema example (only if needed)
    # def get_dynamic_schema():
    #     # Schema that changes based on context
    #     return {"input_data": [{"id": "text", "type": "string"}]}
    # server.input_schema(get_dynamic_schema)  # Register dynamic schema
    
    app = server.get_app()
    
    return app


# ============================================================================
# PATTERN 4: Dynamic schema (optional - only when needed)
# ============================================================================

def pattern4_dynamic_schema():
    """
    Pattern 4: Using dynamic schema (function) - OPTIONAL.
    
    Only use this if your schema needs to change based on context.
    Most agents should use static schemas (Pattern 1, 2, or 3).
    """
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_key"
    )
    
    async def process_job(identifier: str, input_data: dict):
        return {"result": "done"}
    
    # Dynamic schema - only use if schema needs to vary
    def get_input_schema():
        """
        Dynamic schema function - use only if schema needs to change.
        Examples: user permissions, subscription level, time of day, etc.
        """
        # Example: vary schema based on some condition
        from datetime import datetime
        is_business_hours = 9 <= datetime.now().hour <= 17
        
        base_schema = {
            "input_data": [
                {"id": "text", "type": "string", "name": "Text"}
            ]
        }
        
        if is_business_hours:
            # Add extra field during business hours
            base_schema["input_data"].append({
                "id": "priority",
                "type": "option",
                "name": "Priority"
            })
        
        return base_schema
    
    # Use dynamic schema (function)
    app = create_masumi_app(
        config=config,
        agent_identifier="my-agent",
        start_job_handler=process_job,
        input_schema_handler=get_input_schema  # Pass function for dynamic schema
    )
    
    return app


# ============================================================================
# Why This Design Matters
# ============================================================================

"""
KEY INSIGHT: If handlers were required in __init__, you couldn't use decorators!

Decorators need the object to exist FIRST, then they register functions on it.

Example of what decorators do:
    @server.start_job
    async def my_func(...):
        ...

This is equivalent to:
    async def my_func(...):
        ...
    server.start_job(my_func)  # Register after function is defined

But if __init__ required handlers:
    server = MasumiAgentServer(..., start_job_handler=???)  
    # Problem: my_func doesn't exist yet! Can't use decorator syntax.

By allowing None initially, we can:
1. Create the object
2. Define functions
3. Register them with decorators

This gives maximum flexibility!

SCHEMA TYPES:
- Static schema (dict): RECOMMENDED - Most agents use fixed input schemas
- Dynamic schema (callable): OPTIONAL - Only if schema needs to change based on
  context (e.g., user permissions, configuration, time, etc.)
"""

if __name__ == "__main__":
    print("This file demonstrates different usage patterns.")
    print("Run each function to see how handlers can be registered.")
    print("\nPattern 1: Functional style with static schema (most common)")
    print("Pattern 2: Decorator style with static schema (alternative)")
    print("Pattern 3: Mixed style (shows flexibility)")
    print("Pattern 4: Dynamic schema (optional - only when needed)")
    print("\nNote: Static schemas (dict) are RECOMMENDED for most agents.")
    print("      Dynamic schemas (function) are OPTIONAL and only needed")
    print("      when schema must change based on context.")

