# test01

A Masumi agent project generated with `masumi scaffold`.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Run the agent:**
   ```bash
   # API mode (default) - runs as FastAPI server
   masumi run main.py
   
   # Standalone mode - executes job directly
   masumi run main.py --standalone
   ```

## Configuration

### Required Environment Variables

- `AGENT_IDENTIFIER`: Your agent ID (get it after registering on Masumi network)
- `PAYMENT_API_KEY`: Your payment API key
- `SELLER_VKEY`: Your seller wallet verification key

### Optional Environment Variables

- `PAYMENT_SERVICE_URL`: Payment service URL (defaults to production)
- `NETWORK`: Network to use - 'Preprod' or 'Mainnet' (defaults to 'Preprod')
- `PORT`: Port to bind to (defaults to 8080)

### Database Configuration

This project uses **Mongodb** for data storage.
See `.env` file for database connection settings.

### Framework

This project uses **Langchain** for agent orchestration.

### Additional Libraries

This project includes:
- Openai

## Project Structure

```
.
├── main.py           # Entry point - run this to start the agent
├── agent.py          # Agent logic - implement your agentic behavior here
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (create from .env.example)
├── .env.example      # Environment variables template
└── README.md         # This file
```

## Development

### Running Locally

1. Set up your `.env` file with test values
2. Run in standalone mode for testing:
   ```bash
   masumi run main.py --standalone --input '{"text": "Hello World"}'
   ```

### Deploying

1. Register your agent on the Masumi network
2. Get your `AGENT_IDENTIFIER`, `PAYMENT_API_KEY`, and `SELLER_VKEY`
3. Set environment variables in your deployment environment
4. Run the agent in API mode:
   ```bash
   masumi run main.py
   ```

## Documentation

- [Masumi Documentation](https://docs.masumi.network)
- [Masumi CLI Help](https://github.com/masumi-network/masumi)

## License

MIT
