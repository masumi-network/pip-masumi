# Masumi Python SDK

A Python SDK for the Masumi Payment Service, enabling secure blockchain payments between AI agents and users on Cardano.

## Overview

The Masumi SDK provides three main components:
- **Payment**: Seller-side operations (create payment requests, monitor status, complete transactions)
- **Purchase**: Buyer-side operations (create purchases, request refunds)
- **Agent**: Service provider registration on the Masumi network

## Installation

```bash
pip install masumi
```

## Quick Start

```python
from masumi import Config, Agent, Payment, Purchase
import asyncio

# Configure API credentials
config = Config(
    registry_service_url="https://registry.masumi.network/api/v1",
    registry_api_key="your_registry_api_key",
    payment_service_url="https://payment.masumi.network/api/v1",
    payment_api_key="your_payment_api_key"
)

# 1. Register agent (one-time setup)
agent = Agent(
    name="My AI Service",
    config=config,
    description="AI agent for processing tasks",
    # ... other parameters
)
await agent.register()

# 2. Create payment request (seller)
payment = Payment(
    agent_identifier="your_agent_id",
    config=config,
    identifier_from_purchaser="buyer_hex_id"
)
result = await payment.create_payment_request()

# 3. Create purchase (buyer)
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
    registry_service_url="https://registry.masumi.network/api/v1",
    registry_api_key="your_registry_api_key",
    payment_service_url="https://payment.masumi.network/api/v1", 
    payment_api_key="your_payment_api_key"
)
```

### Agent
Registers service providers on the Masumi network to receive payments.

**Methods:**
- `register()` - One-time blockchain registration
- `check_registration_status(wallet_vkey)` - Verify registration confirmed
- `get_selling_wallet_vkey(network)` - Get wallet key for payments

```python
agent = Agent(
    name="My AI Service",
    config=config,
    description="AI processing service",
    api_base_url="https://myservice.com/api",
    author_name="John Doe",
    author_contact="john@example.com",
    author_organization="Company Inc",
    capability_name="text-processing",
    capability_version="1.0.0",
    pricing_unit="lovelace",
    pricing_quantity="10000000",
    network="Preprod"
)
await agent.register()
```

### Payment
Manages payment requests from the seller's perspective.

**Key Methods:**
- `create_payment_request()` - Create a new payment request
- `check_payment_status()` - Check status of payments
- `complete_payment(blockchain_identifier, result_hash)` - Submit work results
- `start_status_monitoring(callback, check_interval)` - Monitor payment status with callback
- `authorize_refund(blockchain_identifier)` - Authorize a refund request

```python
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
result_hash = create_masumi_output_hash({"result": "completed"})
await payment.complete_payment(blockchain_id, result_hash)
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

## Helper Functions

### Hashing Functions
For creating standardized hashes required by the Masumi protocol:

```python
from masumi.helper_functions import create_masumi_input_hash, create_masumi_output_hash

# Hash input data for payment request
input_hash = create_masumi_input_hash(
    {"task": "process this"}, 
    "purchaser_id"
)

# Hash output data for payment completion
output_hash = create_masumi_output_hash({"result": "completed"})
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

## Example: Complete Payment Flow

```python
import asyncio
from masumi import Config, Agent, Payment, Purchase
from masumi.helper_functions import create_masumi_output_hash

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
    output_hash = create_masumi_output_hash({"result": "work completed"})
    await payment.complete_payment(
        payment_result["data"]["blockchainIdentifier"],
        output_hash
    )

asyncio.run(payment_flow())
```

## Documentation

For more information, visit:
- [Masumi Documentation](https://docs.masumi.network/)
- [GitHub Repository](https://github.com/masumi-network/masumi)

## License

MIT License - see LICENSE file for details