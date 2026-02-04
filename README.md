# Masumi Python SDK

[![PyPI version](https://badge.fury.io/py/masumi.svg)](https://badge.fury.io/py/masumi)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/masumi)](https://pepy.tech/project/masumi)


**Build AI agents that accept blockchain payments in 5 minutes.**

```python
from masumi import run

async def process_job(identifier: str, input_data: dict):
    return input_data["text"].upper()

run(process_job, INPUT_SCHEMA)  # That's it! 🎉
```
## Overview

The Masumi SDK provides:
- **Endpoint Abstraction** (NEW): Easy way to create MIP-003 compliant agent APIs with automatic payment handling
- **Payment**: Seller-side operations (create payment requests, monitor status, complete transactions)
- **Purchase**: Buyer-side operations (create purchases, request refunds)

> **Note**: Agents are registered via the admin interface, not programmatically. Get your `agent_identifier` from the admin interface after registration. See the [Masumi Documentation](https://docs.masumi.network/) for more details.

## Installation

**1. Create and activate a virtual environment (recommended):**

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it (Linux/macOS)
source venv/bin/activate

# Or on Windows
venv\Scripts\activate
```

**2. Install Masumi:**

```bash
pip install masumi
```

## Quick Start

### Option 1: Using `masumi.run()` (Simplest - Recommended)

The easiest way to create and run a Masumi agent:

> **Note:** Make sure you've completed the [Installation](#installation) steps first (create venv, install masumi).

**1. Initialize a new agent:**
```bash
masumi init
```



**2. Install dependencies and set up environment:**
```bash
pip install -r requirements.txt
cp .env.example .env  # Edit .env with your credentials
```

**3. Validate your setup:**
```bash
masumi check  # Checks Python version, packages, environment variables, etc.
```

**4. Edit the generated file** to implement your agent logic in the `process_job` function.

**5. Run your agent:**
```bash
# API mode (default) - runs as FastAPI server
# If no file is provided, defaults to main.py
masumi run                    # Runs main.py
masumi run agent.py           # Or specify a file

# Standalone mode - executes job directly without API
masumi run agent.py --standalone --input '{"text": "Hello"}'
```

**Example agent file (`agent.py`):**

> **Note:** Input schemas follow MIP-003 Attachment 01. See [Schema Validator docs](https://docs.masumi.network/documentation/technical-documentation/schema-validator-component) for validation rules.
> 
> **Important:** Your `process_job` function should return a **string**, not a dict. The SDK automatically wraps the result in the response format with `id`, `status`, and `result` fields.

```python
#!/usr/bin/env python3
import os
from masumi import run

# Define agent logic
async def process_job(identifier_from_purchaser: str, input_data: dict):
    text = input_data.get("text", "")
    return text.upper()  # Return a string, not a dict

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
- `AGENT_IDENTIFIER` - Your agent ID from admin interface (OPTIONAL for starting the API, but REQUIRED after registration for the API to work completely)
- `PAYMENT_API_KEY` - Your payment API key from admin interface (REQUIRED)
- `SELLER_VKEY` - Your seller wallet verification key (REQUIRED for API mode and creating purchases)
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
                "name": "Task Description"
            }
        ]
    }

# Create FastAPI app with all MIP-003 endpoints
# Payment creation, monitoring, completion all handled automatically!
# agent_identifier is OPTIONAL for starting the API, but REQUIRED after registration for the API to work completely
# If AGENT_IDENTIFIER environment variable is not set, the server will start with a warning
app = create_masumi_app(
    config=config,
    agent_identifier=os.getenv("AGENT_IDENTIFIER"),  # OPTIONAL: From admin interface (required after registration)
    network=os.getenv("NETWORK", "Preprod"),
    start_job_handler=process_job,
    input_schema_handler=get_input_schema
)

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Option 3: Manual Implementation (Advanced)

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

# agent_identifier is OPTIONAL for starting the API, but REQUIRED after registration for the API to work completely
app = create_masumi_app(
    config=config,
    agent_identifier=os.getenv("AGENT_IDENTIFIER"),  # OPTIONAL: From admin interface (required after registration)
    start_job_handler=your_agent_function,
    input_schema_handler=your_schema_function
)
```

**Important:** `agent_identifier` is optional for starting the API. If not provided, the server will start with a warning and use a placeholder identifier. However, it must be provided after registration for the API to work completely.

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
    # Return a string - the SDK handles response formatting
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
- `check_payment_status_by_identifier(blockchain_identifier)` - Check status of a specific payment
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

The Masumi package includes a CLI for initializing and running agents:

### Init Command

Generate a new agent project:

```bash
# Interactive init (prompts for options)
masumi init

# Non-interactive init with options
masumi init --name my-agent
```

**Adding a Database:**

The `init` command doesn't include database setup by default. If you need database functionality, you can add it manually. Here are examples for common databases:

#### SQLite

1. **Add to `agent.py`:**
   ```python
   import sqlite3
   import os
   
   DB_PATH = os.getenv("DB_PATH", "agent.db")
   
   def get_db():
       conn = sqlite3.connect(DB_PATH)
       return conn
   ```

2. **Use in `process_job`:**
   ```python
   conn = get_db()
   cursor = conn.cursor()
   cursor.execute("INSERT INTO jobs (purchaser_id, input_data) VALUES (?, ?)", 
                  (identifier_from_purchaser, str(input_data)))
   conn.commit()
   conn.close()
   ```

#### PostgreSQL

1. **Add to `requirements.txt`:**
   ```
   psycopg2-binary>=2.9.0
   ```

2. **Add to `agent.py`:**
   ```python
   import psycopg2
   from psycopg2 import pool
   import os
   
   DB_CONFIG = {
       "host": os.getenv("DB_HOST", "localhost"),
       "port": os.getenv("DB_PORT", "5432"),
       "database": os.getenv("DB_NAME", "masumi_agent"),
       "user": os.getenv("DB_USER", "postgres"),
       "password": os.getenv("DB_PASSWORD", "")
   }
   
   db_pool = None
   
   def get_db():
       global db_pool
       if db_pool is None:
           db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)
       return db_pool.getconn()
   
   def return_db(conn):
       db_pool.putconn(conn)
   ```

3. **Add to `.env.example`:**
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=masumi_agent
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   ```

#### MongoDB

1. **Add to `requirements.txt`:**
   ```
   pymongo>=4.0.0
   ```

2. **Add to `agent.py`:**
   ```python
   from pymongo import MongoClient
   import os
   
   MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
   DB_NAME = os.getenv("DB_NAME", "masumi_agent")
   
   client = MongoClient(MONGO_URI)
   db = client[DB_NAME]
   
   def get_db():
       return db
   ```

3. **Add to `.env.example`:**
   ```
   MONGO_URI=mongodb://localhost:27017/
   DB_NAME=masumi_agent
   ```

#### Redis

1. **Add to `requirements.txt`:**
   ```
   redis>=4.0.0
   ```

2. **Add to `agent.py`:**
   ```python
   import redis
   import os
   
   REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
   REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
   REDIS_DB = int(os.getenv("REDIS_DB", "0"))
   
   redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
   
   def get_redis():
       return redis_client
   ```

3. **Add to `.env.example`:**
   ```
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```

### Run Command

Run an agent file:

```bash
# API mode (default) - runs as FastAPI server
# If no file is provided, defaults to main.py
masumi run                    # Runs main.py
masumi run agent.py          # Or specify a file

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

### Human-in-the-Loop (HITL)

Request human input during job execution to pause and resume workflows. This is useful for approvals, additional information, or manual review steps.

**Basic Usage:**

```python
from masumi.hitl import request_input

async def process_job(identifier_from_purchaser: str, input_data: dict):
    # Do some automated work
    result = process_data(input_data)
    
    # Request human approval before proceeding
    approval = await request_input(
        {
            "input_data": [
                {
                    "id": "approve",
                    "type": "boolean",
                    "name": "Approve Result",
                    "data": {
                        "description": f"Approve this result: {result}"
                    }
                }
            ]
        },
        message="Please review and approve the result"
    )
    
    if approval.get("approve"):
        return result
    else:
        return "Processing was rejected"
```

**How It Works:**

1. When `request_input()` is called, execution pauses and the job status is set to `awaiting_input`
2. The `/status` endpoint returns the input schema so clients know what input is needed
3. A human provides input via the `/provide_input` endpoint
4. Execution resumes automatically and `request_input()` returns with the provided data
5. Your agent logic continues with the input

**Testing HITL:**

1. Start your agent: `masumi run`
2. Create a job via `/start_job` endpoint
3. Check status: `GET /status?job_id=<id>` → shows `awaiting_input` with input schema
4. Provide input: `POST /provide_input` with `{"job_id": "<id>", "input_data": {"approve": true}}`
5. Job resumes and completes

**Example: Request Multiple Fields:**

```python
config = await request_input({
    "input_data": [
        {"id": "style", "type": "option", "name": "Style", "data": {"values": ["formal", "casual"]}},
        {"id": "tone", "type": "text", "name": "Tone", "data": {"placeholder": "Enter tone"}}
    ]
})

# Use the provided configuration
style = config.get("style")
tone = config.get("tone")
```

**Note:** The default `provide_input_handler` is automatically configured. You can override it by providing a custom handler to `create_masumi_app()` or `masumi.run()`.

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

- **Python 3.8+** (tested with Python 3.8-3.13)
- aiohttp>=3.8.0
- canonicaljson>=1.6.3
- fastapi>=0.100.0
- uvicorn[standard]>=0.23.0
- pydantic>=2.0.0
- python-dotenv>=0.19.0
- InquirerPy>=0.3.4
- pip-system-certs>=4.0.0

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
```

Run specific test functions:
```bash
pytest masumi/tests/test_endpoints.py::test_start_job_handler_registration
```

### Required Environment Variables

**For Running the Server (Production/Development):**

- `AGENT_IDENTIFIER` (**optional**): Agent identifier from admin interface. The server will start without it (with a warning), but it must be provided after registration for the API to work completely. You can either:
  - Set the environment variable: `export AGENT_IDENTIFIER="your-agent-id"`
  - Pass it directly: `create_masumi_app(agent_identifier="your-agent-id", ...)`
- `SELLER_VKEY` (**required**): Seller wallet verification key from admin interface. The server will raise `ValueError` and refuse to start if this is not provided. You can either:
  - Set the environment variable: `export SELLER_VKEY="your-seller-vkey"`
  - Pass it directly: `create_masumi_app(seller_vkey="your-seller-vkey", ...)`
- `PAYMENT_SERVICE_URL` (required): Payment service API URL
- `PAYMENT_API_KEY` (required): Payment service API key
- `NETWORK` (optional): Network to use (defaults to "Preprod")

**For Running Tests:**

Unit tests (in `test_endpoints.py`) don't require any environment variables as they test the abstraction layer in isolation.

### Test Coverage

To run tests with coverage reporting, first install `pytest-cov`:

```bash
pip install pytest-cov
pytest --cov=masumi --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

**Note:** `pytest-cov` is not included in the package requirements as it's only needed for coverage reporting, not for running tests.

## Contributing

We welcome contributions to the Masumi Python SDK! Here's how you can help:

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/masumi-network/masumi.git
   cd masumi
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

4. **Run tests:**
   ```bash
   pytest
   pytest --cov=masumi --cov-report=html  # With coverage
   ```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Run `ruff check .` to verify code style

### Submitting Changes

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass: `pytest`
4. Submit a pull request with a clear description

### Project Structure

- `masumi/` - Main package code
  - `cli.py` - Command-line interface
  - `server.py` - FastAPI server and endpoint abstraction
  - `payment.py` - Payment operations
  - `purchase.py` - Purchase operations
  - `config.py` - Configuration management
  - `models.py` - Pydantic models
  - `validation.py` - Input validation
  - `job_manager.py` - Job storage and management
  - `tests/` - Test suite

## Documentation

For more information, visit:
- [Masumi Documentation](https://docs.masumi.network/)
- [Quick Start Guide](QUICKSTART.md) - For developers building agents
- [GitHub Repository](https://github.com/masumi-network/masumi)

## License

MIT License - see LICENSE file for details
