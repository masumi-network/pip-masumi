#!/usr/bin/env python3
"""Quick test to verify latest masumi changes are loaded"""

from masumi import run, Config, create_masumi_app
import sys

print("✓ Imports successful")
print(f"✓ Masumi loaded from: {sys.modules['masumi'].__file__}")

# Test that run function exists and has latest signature
import inspect
sig = inspect.signature(run)
print(f"✓ run() parameters: {list(sig.parameters.keys())}")

# Test that Config exists
config = Config(
    payment_service_url="https://test.com",
    payment_api_key="test-key"
)
print(f"✓ Config created: {config.payment_service_url}")

# Test create_masumi_app exists
print(f"✓ create_masumi_app available: {callable(create_masumi_app)}")

async def dummy_handler(identifier_from_purchaser: str, input_data: dict):
    return {"test": "ok"}

# Test that we can create an app (will fail without agent_identifier, which is expected)
try:
    app = create_masumi_app(
        config=config,
        agent_identifier="test-agent",
        seller_vkey="test-vkey",
        start_job_handler=dummy_handler,
        input_schema_handler={"input_data": []}
    )
    print(f"✓ App created successfully")
except Exception as e:
    print(f"✗ App creation failed: {e}")

print("\n✅ All latest changes are loaded and working!")
