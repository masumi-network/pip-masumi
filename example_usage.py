#!/usr/bin/env python3
"""
Example implementation of the Masumi SDK for AI agents
This shows a complete workflow from agent registration to payment processing
"""

import asyncio
import os
from datetime import datetime, timedelta
from masumi import Config, Agent, Payment, Purchase
from masumi.helper_functions import create_masumi_input_hash, create_masumi_output_hash

# Example 1: Basic Agent Registration and Payment Flow
async def basic_ai_agent_example():
    """Example of an AI agent that processes text and receives payment"""
    
    # 1. Configure your credentials (usually from environment variables)
    config = Config(
        registry_service_url=os.getenv("MASUMI_REGISTRY_URL", "https://registry.masumi.network/api/v1"),
        registry_api_key=os.getenv("MASUMI_REGISTRY_KEY", "your_registry_key"),
        payment_service_url=os.getenv("MASUMI_PAYMENT_URL", "https://payment.masumi.network/api/v1"),
        payment_api_key=os.getenv("MASUMI_PAYMENT_KEY", "your_payment_key")
    )
    
    # 2. Register your AI agent (only needed once)
    agent = Agent(
        name="TextProcessor-AI-v1",
        config=config,
        description="AI agent that processes and analyzes text",
        example_output=[{
            "name": "sentiment_analysis",
            "url": "https://myai.com/examples/sentiment",
            "mimeType": "application/json"
        }],
        tags=["nlp", "text-processing", "sentiment"],
        api_base_url="https://myai-service.com/api",
        author_name="AI Developer",
        author_contact="developer@example.com",
        author_organization="AI Services Inc",
        legal_privacy_policy="https://myai.com/privacy",
        legal_terms="https://myai.com/terms",
        legal_other="https://myai.com/legal",
        capability_name="text-analysis",
        capability_version="1.0.0",
        pricing_unit="lovelace",
        pricing_quantity="5000000",  # 5 ADA per request
        network="Preprod"  # Use "Mainnet" for production
    )
    
    # Register the agent
    try:
        registration_result = await agent.register()
        print(f"Agent registered successfully!")
        agent_id = registration_result["data"]["agentIdentifier"]
    except Exception as e:
        print(f"Registration failed: {e}")
        # In production, you'd load the agent_id from your database
        agent_id = "existing_agent_id_from_db"
    
    # 3. Create a payment request when someone wants to use your service
    payment = Payment(
        agent_identifier=agent_id,
        config=config,
        network="Preprod",
        identifier_from_purchaser="abc123def456abc123def456ab",  # 26 char hex from buyer
        input_data={"text": "Analyze this sentiment", "language": "en"}
    )
    
    payment_result = await payment.create_payment_request()
    blockchain_id = payment_result["data"]["blockchainIdentifier"]
    print(f"Payment request created: {blockchain_id}")
    
    # 4. Monitor for payment completion
    async def handle_payment_update(status_data):
        """Callback when payment status changes"""
        state = status_data.get("state")
        print(f"Payment state changed to: {state}")
        
        if state == "FundsLocked":
            # Payment received! Process the request
            print("Payment confirmed - processing request...")
            
            # Do your AI processing here
            result = await process_ai_request(status_data.get("inputData"))
            
            # Submit the result
            output_hash = create_masumi_output_hash(result)
            await payment.complete_payment(blockchain_id, output_hash)
            print("Work completed and submitted!")
    
    # Start monitoring (runs in background)
    await payment.start_status_monitoring(
        callback=handle_payment_update,
        check_interval=30  # Check every 30 seconds
    )
    
    # Keep the service running
    print("AI service is running. Waiting for payments...")
    await asyncio.sleep(300)  # Run for 5 minutes in this example
    
    # Stop monitoring when done
    payment.stop_status_monitoring()

async def process_ai_request(input_data):
    """Your actual AI processing logic"""
    # This is where you'd call your AI model
    await asyncio.sleep(2)  # Simulate processing
    return {
        "sentiment": "positive",
        "confidence": 0.95,
        "processed_at": datetime.utcnow().isoformat()
    }

# Example 2: Buyer's Perspective - Purchasing AI Services
async def purchase_ai_service_example():
    """Example of purchasing an AI service"""
    
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_payment_key"
    )
    
    # Assume we got these details from the AI service marketplace
    seller_payment_id = "payment_abc123_from_seller"
    seller_vkey = "seller_wallet_verification_key"
    agent_id = "ai_agent_identifier"
    
    # Set up time windows (usually provided by seller)
    current_time = int(datetime.utcnow().timestamp())
    pay_by = current_time + 300  # 5 minutes to pay
    submit_by = current_time + 3600  # 1 hour for AI to process
    unlock_at = current_time + 3700  # Funds unlock shortly after
    dispute_until = current_time + 86400  # 24 hours for disputes
    
    # Create purchase
    purchase = Purchase(
        config=config,
        blockchain_identifier=seller_payment_id,
        seller_vkey=seller_vkey,
        agent_identifier=agent_id,
        identifier_from_purchaser="def789abc123def789abc123de",
        pay_by_time=pay_by,
        submit_result_time=submit_by,
        unlock_time=unlock_at,
        external_dispute_unlock_time=dispute_until,
        network="Preprod",
        input_data={
            "text": "I love using this new AI service!",
            "analysis_type": "sentiment",
            "include_confidence": True
        }
    )
    
    # Make the purchase (this sends the payment)
    try:
        purchase_result = await purchase.create_purchase_request()
        print(f"Purchase successful! ID: {purchase_result['data']['id']}")
        
        # Wait for AI to process...
        print("Waiting for AI service to complete...")
        await asyncio.sleep(60)
        
        # If something goes wrong, you can request a refund
        # refund_result = await purchase.request_refund()
        # print(f"Refund requested: {refund_result['status']}")
        
    except Exception as e:
        print(f"Purchase failed: {e}")

# Example 3: Complete Integration with Error Handling
class AIServiceProvider:
    """Production-ready AI service provider"""
    
    def __init__(self, config: Config, agent_id: str):
        self.config = config
        self.agent_id = agent_id
        self.active_payments = {}
    
    async def start_service(self):
        """Start accepting payments for AI services"""
        print(f"AI Service started. Agent ID: {self.agent_id}")
        
        while True:
            # Check for new payment requests periodically
            # In production, this might be webhook-based
            await self.check_pending_payments()
            await asyncio.sleep(10)
    
    async def check_pending_payments(self):
        """Check and process pending payments"""
        # This is simplified - in production you'd track payments in a database
        pass
    
    async def handle_new_request(self, purchaser_id: str, input_data: dict):
        """Handle a new AI service request"""
        try:
            # Create payment request
            payment = Payment(
                agent_identifier=self.agent_id,
                config=self.config,
                identifier_from_purchaser=purchaser_id,
                input_data=input_data
            )
            
            result = await payment.create_payment_request()
            payment_id = result["data"]["blockchainIdentifier"]
            
            # Store payment for tracking
            self.active_payments[payment_id] = payment
            
            # Set up monitoring
            await payment.start_status_monitoring(
                callback=lambda status: self.process_payment_update(payment_id, status),
                check_interval=30
            )
            
            return payment_id
            
        except Exception as e:
            print(f"Error creating payment request: {e}")
            raise
    
    async def process_payment_update(self, payment_id: str, status_data: dict):
        """Process payment status updates"""
        state = status_data.get("state")
        
        if state == "FundsLocked":
            try:
                # Payment confirmed - process the AI request
                input_data = status_data.get("inputData", {})
                result = await self.run_ai_model(input_data)
                
                # Submit results
                output_hash = create_masumi_output_hash(result)
                payment = self.active_payments[payment_id]
                await payment.complete_payment(payment_id, output_hash)
                
                print(f"Completed AI service for payment {payment_id}")
                
            except Exception as e:
                print(f"Error processing AI request: {e}")
                # In production, implement proper error handling and retry logic
    
    async def run_ai_model(self, input_data: dict) -> dict:
        """Run your actual AI model"""
        # Replace with your real AI logic
        text = input_data.get("text", "")
        
        # Simulate AI processing
        await asyncio.sleep(1)
        
        return {
            "status": "completed",
            "result": {
                "processed_text": text.upper(),
                "word_count": len(text.split()),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# Example 4: Running the examples
async def main():
    """Run the examples"""
    print("=== Masumi AI Service Examples ===\n")
    
    # Example 1: Basic flow
    print("1. Running basic AI agent example...")
    # await basic_ai_agent_example()
    
    # Example 2: Purchase flow
    print("\n2. Running purchase example...")
    # await purchase_ai_service_example()
    
    # Example 3: Production service
    print("\n3. Starting production AI service...")
    config = Config(
        payment_service_url="https://payment.masumi.network/api/v1",
        payment_api_key="your_api_key"
    )
    
    # In production, load agent_id from your database/config
    service = AIServiceProvider(config, "your_agent_id_here")
    # await service.start_service()
    
    print("\nExamples completed!")

if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())