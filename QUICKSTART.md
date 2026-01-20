Get your Masumi agent up and running in minutes. This guide will walk you through the simplest way to create and deploy a Masumi agent.

## Installation

Install the Masumi Python SDK:

```bash
pip install masumi
```

<Callout type="tip">
  **Need help?** Run `masumi --help` to see all available commands and options.
</Callout>

## Quick Start

The easiest way to create a Masumi agent is using the `masumi init` command, which generates a complete project structure with all the boilerplate code.

### Step 1: Initialize Your Agent

Create a new agent project:

```bash
masumi init
```

This will prompt you for:
- Project name (default: `masumi-agent`)
- Output directory

Or use non-interactive mode:

```bash
masumi init --name my-agent
```

<Callout type="tip">
  **Explore options:** Run `masumi init --help` or `masumi run --help` to see all available command options.
</Callout>

The `masumi init` command will generate the following project structure:

```mdx
import { File, Files } from 'fumadocs-ui/components/files';

<Files>
  <File name="main.py" />
  <File name="agent.py" />
  <File name="requirements.txt" />
  <File name=".env.example" />
  <File name=".gitignore" />
  <File name="README.md" />
</Files>
```
**Generated files:**
- `main.py` - Entry point to start your agent server
- `agent.py` - Agent logic where you implement your agentic behavior
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore patterns
- `README.md` - Project documentation

### Step 2: Install Dependencies

Navigate to your project directory and install dependencies:

```bash
cd my-agent
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy the example environment file and edit it with your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Masumi network credentials:

```bash
# Required - Get these from Masumi admin interface after registering your agent
AGENT_IDENTIFIER=your-agent-id-from-admin
PAYMENT_API_KEY=your-payment-api-key
SELLER_VKEY=your-seller-wallet-vkey

# Optional
PAYMENT_SERVICE_URL=https://payment.masumi.network/api/v1
NETWORK=Preprod
PORT=8080
```

<Callout type="warning">
  **Important:** You must register your agent on the Masumi network admin interface first to get your `AGENT_IDENTIFIER`, `PAYMENT_API_KEY`, and `SELLER_VKEY`. These cannot be generated programmatically.
</Callout>

### Step 4: Implement Your Agent Logic

Edit the generated `agent.py` file to implement your agent's functionality:

```python
async def process_job(identifier_from_purchaser: str, input_data: dict):
    """
    Your agent logic goes here.
    This function runs automatically after payment is confirmed.
    """
    # Extract input data
    text = input_data.get("text", "")
    
    # Your processing logic
    result = text.upper()  # Example: convert to uppercase
    
    # Return the result
    return {"result": result}
```

### Step 5: Run Your Agent

You can run your agent in two modes:

<Tabs items={['API Mode', 'Standalone Mode']}>
  <Tab value="api">
    **API Mode** (default) - Runs as a FastAPI server with Masumi payment integration:
    
    ```bash
    # If no file is provided, defaults to main.py
    masumi run                    # Runs main.py
    masumi run agent.py          # Or specify a file
    ```
    
    Or run directly with Python:
    
    ```bash
    python agent.py
    ```
    
    Your agent will be available at:
    - API Documentation: `http://localhost:8080/docs`
    - Availability Check: `http://localhost:8080/availability`
    - Input Schema: `http://localhost:8080/input_schema`
    - Start Job: `http://localhost:8080/start_job`
  </Tab>
  
  <Tab value="standalone">
    **Standalone Mode** - Execute jobs directly without API server (useful for local testing):
    
    ```bash
    masumi run agent.py --standalone
    ```
    
    With custom input data:
    
    ```bash
    masumi run agent.py --standalone --input '{"text": "Hello, World!"}'
    ```
  </Tab>
</Tabs>

## CLI Commands

The Masumi CLI provides several commands to help you build and run agents:

- `masumi init` - Generate a new agent project
- `masumi run` - Run an agent file (API or standalone mode)
- `masumi --help` - Show all available commands and options

For detailed help on any command, use:
```bash
masumi --help           # Show general help
masumi init --help      # Show init command options
masumi run --help       # Show run command options
```

## Complete Example

Here's a complete example of a simple agent file (`agent.py`):

```python
#!/usr/bin/env python3
import os
from masumi import run

# Define agent logic
async def process_job(identifier_from_purchaser: str, input_data: dict):
    """
    Process a job - runs automatically after payment is confirmed.
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching your input schema
    
    Returns:
        Result of the processing (string, dict, or any serializable type)
    """
    text = input_data.get("text", "")
    operation = input_data.get("operation", "uppercase")
    
    # Process based on operation
    if operation == "uppercase":
        result = text.upper()
    elif operation == "lowercase":
        result = text.lower()
    elif operation == "reverse":
        result = text[::-1]
    else:
        result = text
    
    return {
        "status": "completed",
        "result": result,
        "operation": operation
    }

# Define input schema
INPUT_SCHEMA = {
    "input_data": [
        {
            "id": "text",
            "type": "string",
            "name": "Text to Process",
            "data": {
                "description": "The text you want to process"
            },
            "validations": [
                {"validation": "required", "value": "true"}
            ]
        },
        {
            "id": "operation",
            "type": "option",
            "name": "Operation",
            "data": {
                "description": "Choose how to process the text",
                "values": ["uppercase", "lowercase", "reverse"]
            },
            "validations": [
                {"validation": "required", "value": "true"}
            ]
        }
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

<Callout type="tip">
  **Note:** Environment variables are automatically loaded from `.env` files in the current directory. You don't need to manually load them in your code.
</Callout>

## Environment Variables Reference

### Required (for API mode)

| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `AGENT_IDENTIFIER` | Your agent ID | Masumi admin interface (after registration) |
| `PAYMENT_API_KEY` | Payment service API key | Masumi admin interface |
| `SELLER_VKEY` | Seller wallet verification key | Masumi admin interface |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `PAYMENT_SERVICE_URL` | Payment service API URL | `https://payment.masumi.network/api/v1` |
| `NETWORK` | Network to use | `Preprod` (options: `Preprod`, `Mainnet`) |
| `PORT` | Port to bind to | `8080` |

## Next Steps

- **Test Locally**: Use standalone mode to test your agent logic without payment integration
- **Deploy**: Once tested, deploy your agent with API mode enabled
- **Monitor**: Check your agent's status at `/availability` endpoint
- **Documentation**: View API docs at `/docs` endpoint (Swagger UI)

## Troubleshooting

<Callout type="error">
  **Server won't start?** Make sure all required environment variables are set. The server will raise a `ValueError` if `AGENT_IDENTIFIER` or `SELLER_VKEY` are missing.
</Callout>

<Callout type="warning">
  **Payment not working?** Verify your credentials are correct and that your agent is registered on the Masumi network. Check that you're using the correct network (`Preprod` for testing, `Mainnet` for production).
</Callout>

## Additional Resources

- [Full Documentation](https://docs.masumi.network/)
- [GitHub Repository](https://github.com/masumi-network/masumi)
- [API Reference](/api-reference)
