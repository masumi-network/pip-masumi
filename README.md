# Masumi Python SDK

A Python SDK for the Masumi Payment Service, enabling secure blockchain payments between AI agents and users on Cardano.

## Overview

The Masumi SDK provides:
- **Endpoint Abstraction** (NEW): Easy way to create MIP-003 compliant agent APIs with automatic payment handling
- **Payment**: Seller-side operations (create payment requests, monitor status, complete transactions)
- **Purchase**: Buyer-side operations (create purchases, request refunds)

> **Note**: Agents are registered via the admin interface, not programmatically. Get your `agent_identifier` from the admin interface after registration.

## Installation

```bash
pip install masumi
```

## Quick Start

### Option 1: Using `masumi.run()` (Simplest - Recommended)

The easiest way to create and run a Masumi agent:

**1. Scaffold a new agent:**
```bash
masumi scaffold
```

This will generate an `agent.py` file with all the boilerplate. You can also specify database and framework:
```bash
masumi scaffold --output my_agent.py --database sqlite --framework langchain
```

**2. Edit the generated file** to implement your agent logic in the `process_job` function.

**3. Run your agent:**
```bash
# API mode (default) - runs as FastAPI server
masumi run agent.py

# Standalone mode - executes job directly without API
masumi run agent.py --standalone --input '{"text": "Hello"}'
```

**Example agent file (`agent.py`):**
```python
#!/usr/bin/env python3
import os
from masumi import run

# Define agent logic
async def process_job(identifier_from_purchaser: str, input_data: dict):
    text = input_data.get("text", "")
    return {"result": text.upper()}

# Define input schema
INPUT_SCHEMA = {
    "input_data": [
        {"id": "text", "type": "string", "name": "Text"}
    ]
}

# Main entry point
if __name__ == "__main__":
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
        # config, agent_identifier, network loaded from env vars automatically
    )
```

**Required environment variables for API mode:**
- `AGENT_IDENTIFIER` - Your agent ID from admin interface (REQUIRED)
- `PAYMENT_API_KEY` - Your payment API key (REQUIRED)
- `SELLER_VKEY` - Your seller wallet verification key (REQUIRED)
- `PAYMENT_SERVICE_URL` - Payment service URL (optional, defaults to production)
- `NETWORK` - Network to use: "Preprod" or "Mainnet" (optional, defaults to "Preprod")

**Note:** Environment variables can be set in a `.env` file. `.env` files are automatically loaded by `masumi.run()` from the current directory.

### Option 2: Using Endpoint Abstraction (Advanced)

Create a MIP-003 compliant agent API with minimal code:

```python
from masumi import create_masumi_app, Config
import uvicorn
import os

# Configure API credentials
config = Config(
    payment_service_url=os.getenv("PAYMENT_SERVICE_URL"),
    payment_api_key=os.getenv("PAYMENT_API_KEY")
)

# Define your agent logic - runs when payment is confirmed
async def process_job(identifier_from_purchaser: str, input_data: dict):
    text = input_data.get("text", "")
    result = f"Processed: {text}"
    return result

# Define input schema
def get_input_schema():
    return {
        "input_data": [
            {
                "id": "text",
                "type": "string",
                "name": "Task Description",
                "data": {"description": "The text input for the AI task"}
            }
        ]
    }

# Create FastAPI app with all MIP-003 endpoints
# Payment creation, monitoring, completion all handled automatically!
# agent_identifier is REQUIRED - get it from admin interface after registering your agent
# If AGENT_IDENTIFIER environment variable is not set, the server will raise ValueError
app = create_masumi_app(
    config=config,
    agent_identifier=os.getenv("AGENT_IDENTIFIER"),  # REQUIRED: From admin interface
    network=os.getenv("NETWORK", "Preprod"),
    start_job_handler=process_job,
    input_schema_handler=get_input_schema
)

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Option 2: Manual Implementation (Advanced)

For more control, use the Payment and Purchase classes directly:

```python
from masumi import Config, Payment, Purchase
import asyncio

config = Config(
    payment_service_url="https://payment.masumi.network/api/v1",
    payment_api_key="your_payment_api_key"
)

# Create payment request (seller)
payment = Payment(
    agent_identifier="your_agent_id",  # From admin interface
    config=config,
    identifier_from_purchaser="buyer_hex_id"
)
result = await payment.create_payment_request()

# Create purchase (buyer)
purchase = Purchase(
    config=config,
    blockchain_identifier=result["data"]["blockchainIdentifier"],
    # ... payment details
)
await purchase.create_purchase_request()
```

## Core Classes

### Config
Manages API endpoints and authentication keys.

```python
config = Config(
    payment_service_url="https://payment.masumi.network/api/v1", 
    payment_api_key="your_payment_api_key"
)
```

### Endpoint Abstraction

The easiest way to create MIP-003 compliant agent APIs. Handles all endpoints, payment flow, and job management automatically.

**Using `create_masumi_app()` (simplest):**

```python
from masumi import create_masumi_app, Config
import os

# agent_identifier is REQUIRED - get it from admin interface
app = create_masumi_app(
    config=config,
    agent_identifier=os.getenv("AGENT_IDENTIFIER"),  # REQUIRED: From admin interface
    start_job_handler=your_agent_function,
    input_schema_handler=your_schema_function
)
```

**Important:** `agent_identifier` is required. If not provided directly or via the `AGENT_IDENTIFIER` environment variable, the server will raise a `ValueError` and refuse to start.

**Using `MasumiAgentServer` (more control):**

```python
from masumi import MasumiAgentServer, Config

server = MasumiAgentServer(
    config=config,
    agent_identifier="your_agent_id",
    network="Preprod"
)

@server.start_job
async def my_agent_logic(identifier_from_purchaser: str, input_data: dict):
    # Your agent logic here
    return result

@server.input_schema
def get_schema():
    return {"input_data": [...]}

app = server.get_app()
```

**Features:**
- Automatic MIP-003 endpoint setup (`/start_job`, `/status`, `/availability`, `/input_schema`, etc.)
- Automatic payment request creation and monitoring
- Automatic payment completion after job execution
- Built-in input validation
- Automatic OpenAPI/Swagger documentation
- Pluggable job storage (default: in-memory, can use custom databases)

**Job Storage:**

Default uses in-memory storage (for development). For production, implement a custom `JobStorage`:

```python
from masumi.job_manager import JobStorage

class MyDatabaseStorage(JobStorage):
    async def create_job(self, job_id: str, job_data: dict):
        # Save to your database
        pass
    # ... implement other methods

app = create_masumi_app(
    ...,
    job_storage=MyDatabaseStorage()
)
```

### Payment
Manages payment requests from the seller's perspective.

**Key Methods:**
- `create_payment_request()` - Create a new payment request
- `check_payment_status()` - Check status of payments
- `complete_payment(blockchain_identifier, output_string)` - Submit work results
- `start_status_monitoring(callback, check_interval)` - Monitor payment status with callback
- `authorize_refund(blockchain_identifier)` - Authorize a refund request

```python
import json

payment = Payment(
    agent_identifier="your_agent_id",
    config=config,
    network="Preprod",
    identifier_from_purchaser="buyer_hex_id",  # 26 char hex string
    input_data={"task": "process this data"}
)

# Create payment request
result = await payment.create_payment_request()
blockchain_id = result["data"]["blockchainIdentifier"]

# Monitor status
await payment.start_status_monitoring(
    callback=handle_payment_update,
    check_interval=30
)

# Complete payment with results
output_string = json.dumps({"result": "completed"}, separators=(",", ":"), ensure_ascii=False)
await payment.complete_payment(blockchain_id, output_string)
```

### Purchase
Handles purchase requests from the buyer's perspective.

**Key Methods:**
- `create_purchase_request()` - Create a purchase and pay
- `request_refund()` - Request a refund for the purchase
- `cancel_refund_request()` - Cancel a pending refund request

```python
purchase = Purchase(
    config=config,
    blockchain_identifier="payment_id_from_seller",
    seller_vkey="seller_wallet_vkey",
    agent_identifier="agent_id",
    identifier_from_purchaser="buyer_hex_id",  # 26 char hex string
    pay_by_time=1234567890,  # Unix timestamps
    submit_result_time=1234567890,
    unlock_time=1234567890,
    external_dispute_unlock_time=1234567890,
    network="Preprod",
    input_data={"task": "process this"}
)

# Create purchase
result = await purchase.create_purchase_request()

# Request refund if needed
refund_result = await purchase.request_refund()

# Or cancel refund request
cancel_result = await purchase.cancel_refund_request()
```

## CLI Commands

The Masumi package includes a CLI for scaffolding and running agents:

### Scaffold Command

Generate a new agent file with database and framework integration:

```bash
# Interactive scaffold (prompts for options)
masumi scaffold

# Non-interactive scaffold with options
masumi scaffold --output my_agent.py --database sqlite --framework langchain
```

**Supported databases:**
- `sqlite` - SQLite (file-based, no setup needed)
- `postgresql` - PostgreSQL (requires connection string)
- `mongodb` - MongoDB (requires connection string)
- `redis` - Redis (for caching/sessions)

**Supported frameworks:**
- `langchain` - LangChain (LLM orchestration)
- `crewai` - CrewAI (multi-agent framework)
- `autogen` - AutoGen (conversational AI agents)

### Run Command

Run an agent file:

```bash
# API mode (default) - runs as FastAPI server
masumi run agent.py

# Standalone mode - executes job directly without API
masumi run agent.py --standalone

# Standalone with custom input data
masumi run agent.py --standalone --input '{"text": "Hello, World!"}'
```

You can also run files directly with Python:
```bash
python agent.py  # Runs in API mode by default
```

## Helper Functions

### Hashing Functions
For creating standardized hashes required by the Masumi protocol:

```python
import json
from masumi.helper_functions import create_masumi_input_hash, create_masumi_output_hash

# Hash input data for payment request
input_hash = create_masumi_input_hash(
    {"task": "process this"}, 
    "purchaser_id"
)

# Hash output data for payment completion
output_hash = create_masumi_output_hash("work completed", "purchaser_id")

# If your AI result is structured data, serialize it first:
output_string = json.dumps({"result": "completed"}, separators=(",", ":"), ensure_ascii=False)
output_hash = create_masumi_output_hash(output_string, "purchaser_id")
```

## Time-based Transaction Flow

The Masumi protocol uses time-based controls for secure transactions:

1. **pay_by_time** - Deadline for buyer to make payment
2. **submit_result_time** - Deadline for seller to submit work results  
3. **unlock_time** - Funds unlock to seller if results were submitted
4. **external_dispute_unlock_time** - Final resolution time for disputes

## Networks

- **Preprod** - Test network (default)
- **Mainnet** - Production network

## Requirements

- Python 3.8+
- aiohttp
- canonicaljson
- fastapi
- uvicorn
- pydantic

Install all dependencies:
```bash
pip install masumi
```

## Example: Complete Payment Flow

```python
import asyncio
import json
from masumi import Config, Payment, Purchase, create_masumi_app

async def payment_flow():
    # Setup
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_api_key"
    )
    
    # Seller creates payment request
    payment = Payment(
        agent_identifier="agent_123",
        config=config,
        identifier_from_purchaser="abcdef1234567890abcdef12"
    )
    payment_result = await payment.create_payment_request()
    
    # Buyer creates purchase
    purchase = Purchase(
        config=config,
        blockchain_identifier=payment_result["data"]["blockchainIdentifier"],
        # ... other required parameters
    )
    purchase_result = await purchase.create_purchase_request()
    
    # Seller completes work and submits results
    output_string = json.dumps({"result": "work completed"}, separators=(",", ":"), ensure_ascii=False)
    await payment.complete_payment(
        payment_result["data"]["blockchainIdentifier"],
        output_string
    )

asyncio.run(payment_flow())
```

## Testing

The package includes a comprehensive test suite. To run tests:

### Installation

First, install the package with test dependencies:

```bash
pip install -r requirements.txt
# Or install in development mode:
pip install -e .
```

### Running Tests

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test files:
```bash
# Run endpoint abstraction tests
pytest masumi/tests/test_endpoints.py

# Run payment/purchase tests
pytest masumi/tests/test_masumi.py
```

Run specific test functions:
```bash
pytest masumi/tests/test_endpoints.py::test_start_job_handler_registration
```

### Required Environment Variables

**For Running the Server (Production/Development):**

- `AGENT_IDENTIFIER` (**required**): Agent identifier from admin interface. The server will raise `ValueError` and refuse to start if this is not provided. You can either:
  - Set the environment variable: `export AGENT_IDENTIFIER="your-agent-id"`
  - Pass it directly: `create_masumi_app(agent_identifier="your-agent-id", ...)`
- `SELLER_VKEY` (**required**): Seller wallet verification key from admin interface. The server will raise `ValueError` and refuse to start if this is not provided. You can either:
  - Set the environment variable: `export SELLER_VKEY="your-seller-vkey"`
  - Pass it directly: `create_masumi_app(seller_vkey="your-seller-vkey", ...)`
- `PAYMENT_SERVICE_URL` (required): Payment service API URL
- `PAYMENT_API_KEY` (required): Payment service API key
- `NETWORK` (optional): Network to use (defaults to "Preprod")

**For Running Tests:**

- `TEST_AGENT_ID` (optional): Agent identifier from admin interface. Defaults to `"test-agent-id-from-admin"` for unit tests.
- `TEST_SELLER_VKEY` (optional): Seller wallet verification key. Defaults to `"test-seller-vkey-from-admin"` for unit tests.

For integration tests that interact with the actual payment service, you'll also need:

- `PAYMENT_SERVICE_URL`: Payment service API URL (defaults to test URL in fixtures)
- `PAYMENT_API_KEY`: Payment service API key (defaults to test key in fixtures)

**Example:**
```bash
export TEST_AGENT_ID="your-agent-id-from-admin"
export TEST_SELLER_VKEY="your-seller-vkey"
pytest
```

**Note:** Unit tests (in `test_endpoints.py`) don't require these variables as they test the abstraction layer in isolation. Integration tests (in `test_masumi.py`) that interact with the payment service may require valid credentials.

### Test Coverage

To run tests with coverage reporting, first install `pytest-cov`:

```bash
pip install pytest-cov
pytest --cov=masumi --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

**Note:** `pytest-cov` is not included in the package requirements as it's only needed for coverage reporting, not for running tests.

## Documentation

For more information, visit:
- [Masumi Documentation](https://docs.masumi.network/)
- [GitHub Repository](https://github.com/masumi-network/masumi)

## License

MIT License - see LICENSE file for details
