from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import asyncio
import logging
import json
from typing import List, Optional, Dict, Any, Set
import aiohttp
from .config import Config
from .helper_functions import create_masumi_input_hash, create_masumi_output_hash, setup_logging
from .models import PaymentOnChainState, PaymentNextAction

logger = setup_logging(__name__)

@dataclass
class Amount:
    """
    Represents a payment amount in a specific unit.
    
    Attributes:
        amount (int): The payment amount (e.g., 1000000 for 1 ADA)
        unit (str): The currency unit (e.g., 'lovelace' for ADA)
    """
    amount: int
    unit: str

class Payment:
    """
    Handles Cardano blockchain payment operations including creation, monitoring, and completion.
    
    This class manages payment requests and their lifecycle, supporting multiple concurrent
    payment tracking. It uses the Masumi payment service for all payment operations.
    
    Attributes:
        agent_identifier (str): Unique identifier for the agent making payments
        amounts (List[Amount]): List of payment amounts and their units
        network (str): Network to use ('Preprod' or 'Mainnet')
        payment_type (str): Type of payment (fixed to 'WEB3_CARDANO_V1')
        payment_ids (Set[str]): Set of active payment IDs being tracked
        config (Config): Configuration for API endpoints and authentication
    """

    def __init__(self, agent_identifier: str, amounts: Optional[List[Amount]] = None, 
                 config: Config = None, network: str = "Preprod", 
                 preprod_address: Optional[str] = None,
                 mainnet_address: Optional[str] = None,
                 identifier_from_purchaser: str = "default_purchaser_id",
                 input_data: Optional[dict] = None):
        """
        Initialize a new Payment instance.
        
        Args:
            agent_identifier (str): Unique identifier for the agent
            amounts (List[Amount], optional): DEPRECATED - Payment amounts no longer used in API
            config (Config): Configuration object with API details
            network (str, optional): Network to use. Defaults to "PREPROD"
            preprod_address (str, optional): Custom preprod contract address
            mainnet_address (str, optional): Custom mainnet contract address
            identifier_from_purchaser (str): Identifier provided by purchaser. 
                                           Defaults to 'default_purchaser_id'
            input_data (str, optional): Input data for hashing
        """
        logger.info(f"Initializing Payment instance for agent {agent_identifier} on {network} network")
        self.agent_identifier = agent_identifier
        self.preprod_address = preprod_address or config.preprod_address
        self.mainnet_address = mainnet_address or config.mainnet_address
        self.amounts = amounts
        self.network = network
        self.payment_type = "Web3CardanoV1"
        self.payment_ids: Set[str] = set()
        self._callback_triggered_ids: Set[str] = set()
        self._callback_tasks: Set[asyncio.Task] = set()  # Track callback tasks to prevent memory leaks
        self.identifier_from_purchaser = identifier_from_purchaser
        self._status_check_task: Optional[asyncio.Task] = None
        self.config = config
        self._headers = {
            "token": config.payment_api_key,
            "Content-Type": "application/json"
        }
        # Hash the input data if provided
        self.input_hash = (
            create_masumi_input_hash(input_data, self.identifier_from_purchaser)
            if input_data
            else None
        )
        logger.debug(f"Input data: {input_data}")
        logger.debug(f"Input hash: {self.input_hash}")
        #logger.debug(f"Payment amounts configured: {[f'{a.amount} {a.unit}' for a in amounts]}")
        logger.debug(f"Using purchaser identifier: {self.identifier_from_purchaser}")

    async def create_payment_request(self, metadata: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new payment request.
        
        Creates a payment request with the specified amounts and adds the payment ID
        to the tracking set. The payment deadline is automatically set to 12 hours
        from creation.
        
        Args:
            metadata (str, optional): Private metadata to be stored with the payment request
        
        Returns:
            Dict[str, Any]: Response from the payment service containing payment details
                and the time values (submitResultTime, unlockTime, externalDisputeUnlockTime)
            
        Raises:
            ValueError: If the request is invalid
            Exception: If there's a network or server error
        """
        logger.info(f"Creating new payment request for agent {self.agent_identifier}")
        
        # Set payByTime to 12 hours from now
        pay_by_time = datetime.now(timezone.utc) + timedelta(hours=12)
        pay_by_time_str = pay_by_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Set submitResultTime to 24 hours from now (after payByTime)
        submit_result_time = datetime.now(timezone.utc) + timedelta(hours=24)
        submit_result_time_str = submit_result_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        logger.debug(f"Payment deadline (payByTime) set to {pay_by_time_str}")
        logger.debug(f"Submit result deadline set to {submit_result_time_str}")

        payload = {
            "agentIdentifier": self.agent_identifier,
            "network": self.network,
            "paymentType": self.payment_type,
            "payByTime": pay_by_time_str,
            "submitResultTime": submit_result_time_str,
            "identifierFromPurchaser": self.identifier_from_purchaser
        }

        # Add input hash to payload if available
        if self.input_hash:
            payload["inputHash"] = self.input_hash

        # Add metadata if provided
        if metadata:
            payload["metadata"] = metadata

        logger.info(f"Payment request payload prepared: {payload}")

        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                logger.debug("Sending payment request to API")
                async with session.post(
                    f"{self.config.payment_service_url}/payment/",
                    headers=self._headers,
                    json=payload
                ) as response:
                    if response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Bad request error: {error_text}")
                        raise ValueError(f"Bad request: {error_text}")
                    if response.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        raise ValueError("Unauthorized: Invalid API key")
                    if response.status == 500:
                        logger.error("Internal server error from payment service")
                        raise Exception("Internal server error")
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Payment request failed with status {response.status}: {error_text}")
                        raise Exception(f"Payment request failed: {error_text}")
                    
                    result = await response.json()
                    new_payment_id = result["data"]["blockchainIdentifier"]
                    self.payment_ids.add(new_payment_id)
                    logger.info(f"Payment request created successfully. ID: {new_payment_id}")
                    logger.info(f"Payment Details: {json.dumps(result['data'], indent=2)}")
                    time_values = {
                        "payByTime": result["data"]["payByTime"],
                        "submitResultTime": result["data"]["submitResultTime"],
                        "unlockTime": result["data"]["unlockTime"],
                        "externalDisputeUnlockTime": result["data"]["externalDisputeUnlockTime"]
                    }
                    
                    # Add time values to the result for easy access
                    result["time_values"] = time_values
                    
                    #logger.info(f"Payment request created successfully. Payment ID: {new_payment_id}")
                    logger.debug(f"Time values: {time_values}")
                    logger.debug(f"Full payment response: {result}")
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"Network error during payment request: {str(e)}")
            raise

    async def check_payment_status_by_identifier(self, blockchain_identifier: str) -> Dict[str, Any]:
        """
        Check the status of a specific payment by blockchain identifier.
        
        Args:
            blockchain_identifier (str): The blockchain identifier of the payment to check
            
        Returns:
            Dict[str, Any]: Response containing the payment status
            
        Raises:
            ValueError: If blockchain_identifier is empty
            Exception: If status check fails
        """
        if not blockchain_identifier:
            raise ValueError("blockchain_identifier cannot be empty")
        
        logger.debug(f"Checking status for payment: {blockchain_identifier}")
        
        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                # Build request body
                payload = {
                    'network': self.network,
                    'blockchainIdentifier': blockchain_identifier,
                    'includeHistory': "false"
                }
                
                url = f"{self.config.payment_service_url}/payment/resolve-blockchain-identifier"
                logger.debug(f"Calling payment status endpoint: {url} with payload: network={self.network}, blockchainIdentifier={blockchain_identifier[:8]}...")
                
                async with session.post(
                    url,
                    headers=self._headers,
                    json=payload
                ) as response:
                    logger.debug(f"Payment status check response status: {response.status} for payment {blockchain_identifier}")
                    
                    if response.status == 404:
                        error_text = await response.text()
                        logger.warning(f"Payment {blockchain_identifier} not found: {error_text}")
                        return {
                            "status": "error",
                            "message": f"Payment {blockchain_identifier} not found",
                            "data": None
                        }
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Status check failed for payment {blockchain_identifier} with status {response.status}: {error_text}")
                        raise Exception(f"Status check failed: {error_text}")
                    
                    result = await response.json()
                    logger.debug(f"Successfully received status response for payment {blockchain_identifier}")
                    logger.debug(f"Payment {blockchain_identifier} status: {result.get('data', {}).get('onChainState', 'Unknown')}")
                    return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during status check for payment {blockchain_identifier}: {str(e)}")
            raise

    async def complete_payment(self, blockchain_identifier: str, job_output: str) -> Dict[str, Any]:
        """
        Complete a payment by submitting the result hash.
        
        Args:
            blockchain_identifier (str): The blockchain identifier of the payment to complete
            job_output (str): The raw output string produced by the job
            
        Returns:
            Dict[str, Any]: Response from the payment service
            
        Raises:
            ValueError: If the request is invalid
            Exception: If there's a network or server error
        """
        #logger.info(f"Completing payment with blockchain identifier: {blockchain_identifier}")
        
        if not isinstance(job_output, str):
            raise TypeError("job_output must be a string")

        result_hash = create_masumi_output_hash(
            job_output,
            self.identifier_from_purchaser
        )

        # Create the payload for the submit-result endpoint
        payload = {
            "network": self.network,
            "blockchainIdentifier": blockchain_identifier,
            "submitResultHash": result_hash
        }
        
        logger.debug(f"Payment completion payload: {payload}")
        
        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                logger.debug("Sending payment completion request to API")
                async with session.post(
                    f"{self.config.payment_service_url}/payment/submit-result",
                    headers=self._headers,
                    json=payload
                ) as response:
                    if response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Bad request error: {error_text}")
                        raise ValueError(f"Bad request: {error_text}")
                    if response.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        raise ValueError("Unauthorized: Invalid API key")
                    if response.status == 500:
                        logger.error("Internal server error from payment service")
                        raise Exception("Internal server error")
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Payment completion failed with status {response.status}: {error_text}")
                        # Log the payload that failed
                        logger.error(f"Failed payload: {payload}")
                        raise Exception(f"Payment completion failed (status {response.status}): {error_text}")
                    
                    result = await response.json()
                    logger.info(f"Payment completion request successful for {blockchain_identifier}")
                    logger.debug(f"Payment completion response: {result}")
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"Network error during payment completion: {str(e)}")
            raise

    async def start_status_monitoring(self, callback=None, interval_seconds: int = 10) -> None:
        """
        Start monitoring payment status at regular intervals.
        
        Args:
            callback (Callable, optional): Function to call when a payment is ready to process.
                The callback is triggered when payment reaches either:
                - FundsLocked state (PaymentOnChainState.FUNDS_LOCKED) for paid agents
                - FundsOrDatumInvalid state (PaymentOnChainState.FUNDS_OR_DATUM_INVALID) for free agents ONLY
                  (validated by checking if price/amount is 0 in payment data)
                Note: For paid agents, FundsOrDatumInvalid means an actual error and callback is NOT triggered.
                The function will receive the full payment dict as its parameter.
                Can be either a regular function or an async function.
                The callback runs in a separate task to avoid blocking the monitoring loop.
                If the callback fails, the payment will remain in tracking for retry on the next interval.
            interval_seconds (int, optional): Interval between status checks in seconds. 
                                             Defaults to 10.
        """
        if self._status_check_task is not None:
            logger.warning("Status monitoring already running, stopping previous task")
            self.stop_status_monitoring()
        
        logger.info(f"Starting payment status monitoring with {interval_seconds} second interval")
        
        async def monitor_task():
            """
            Granular monitoring task that checks each payment individually using 
            /payment/resolve-blockchain-identifier endpoint.
            
            This approach:
            - Reduces network bandwidth by only fetching specific payments
            - Reduces compute/database load on payment service
            - Allows for staggered checks to avoid burst traffic
            - Enables per-payment interval optimization
            """
            logger.info("Payment status monitoring task started (granular mode)")
            
            # Track last check time for each payment to enable staggered checking
            payment_check_times: Dict[str, float] = {}
            
            while True:
                try:
                    if not self.payment_ids:
                        logger.debug("No payment IDs to monitor, waiting for next interval")
                        await asyncio.sleep(interval_seconds)
                        continue
                    
                    current_time = asyncio.get_event_loop().time()
                    payments_to_check = []
                    
                    # Determine which payments need checking based on their last check time
                    # Stagger checks to avoid burst traffic
                    for payment_id in list(self.payment_ids):
                        last_check = payment_check_times.get(payment_id, 0)
                        time_since_check = current_time - last_check
                        
                        # Check if enough time has passed for this payment
                        if time_since_check >= interval_seconds:
                            payments_to_check.append(payment_id)
                    
                    if not payments_to_check:
                        # All payments were recently checked, wait a bit before next round
                        await asyncio.sleep(min(interval_seconds, 5))
                        continue
                    
                    logger.debug(f"Checking {len(payments_to_check)} payment(s) individually using resolve-blockchain-identifier")
                    
                    payments_to_remove = []
                    successful_checks = 0
                    failed_checks = 0
                    
                    # Check each payment individually with small stagger to avoid burst
                    for idx, payment_id in enumerate(payments_to_check):
                        try:
                            # Small stagger between checks (100ms) to avoid overwhelming the service
                            if idx > 0:
                                await asyncio.sleep(0.1)
                            
                            logger.debug(f"Checking status for payment {payment_id[:8]}... using resolve-blockchain-identifier")
                            result = await self.check_payment_status_by_identifier(payment_id)
                            
                            # Update last check time
                            payment_check_times[payment_id] = current_time
                            
                            # Handle case where payment is not found or has error status
                            if result.get("status") == "error" or not result.get("data"):
                                logger.info(f"Payment {payment_id[:8]}... awaiting on-chain settlement (this is normal). Will check again in {interval_seconds} seconds")
                                failed_checks += 1
                                continue
                            
                            successful_checks += 1
                            payment = result.get("data", {})
                            on_chain_state = payment.get("onChainState")
                            next_action = payment.get("NextAction", {}).get("requestedAction")
                            
                            # Handle case where payment exists but hasn't settled on-chain yet (onChainState is null)
                            if on_chain_state is None:
                                logger.info(f"Payment {payment_id[:8]}... awaiting on-chain settlement (this is normal). Will check again in {interval_seconds} seconds")
                                continue
                            
                            logger.debug(f"Payment {payment_id[:8]}...: state={on_chain_state}, action={next_action}")

                            # Determine if we should trigger the callback based on on-chain state
                            should_trigger_callback = False

                            # FundsLocked: Always valid - payment received and locked (normal paid agents)
                            if on_chain_state == PaymentOnChainState.FUNDS_LOCKED.value:
                                should_trigger_callback = True

                            # FundsOrDatumInvalid: Only valid for free agents (0 cost)
                            # For paid agents, this state means funds/datum are genuinely invalid (wrong amount, etc.)
                            elif on_chain_state == PaymentOnChainState.FUNDS_OR_DATUM_INVALID.value:
                                # Check if this is a free agent by looking for price/amount in payment data
                                # The payment service should include pricing info in the payment dict
                                is_free_agent = False

                                # Check various possible fields that might indicate free/0-cost
                                if "price" in payment and payment["price"] == 0:
                                    is_free_agent = True
                                elif "amount" in payment and payment["amount"] == 0:
                                    is_free_agent = True
                                elif "amounts" in payment and (not payment["amounts"] or all(a.get("amount", 1) == 0 for a in payment["amounts"])):
                                    is_free_agent = True

                                if is_free_agent:
                                    logger.info(f"Payment {payment_id[:8]}... is a free agent (0 cost), accepting FundsOrDatumInvalid state")
                                    should_trigger_callback = True
                                else:
                                    logger.error(f"Payment {payment_id[:8]}... reached FundsOrDatumInvalid state but is NOT a free agent - this indicates invalid funds or datum. Not triggering callback.")
                                    logger.error(f"Payment data: {payment}")
                                    # Do not trigger callback - this is a genuine error for paid agents

                            # Trigger callback if valid and not already triggered
                            if should_trigger_callback and payment_id not in self._callback_triggered_ids:
                                logger.info(f"Payment {payment_id[:8]}... reached {on_chain_state} state, triggering callback")
                                self._callback_triggered_ids.add(payment_id)
                                
                                # Call the callback function if provided
                                if callback:
                                    async def run_callback():
                                        """Run callback in a separate task to avoid blocking"""
                                        try:
                                            logger.info(f"Calling callback function for payment {payment_id[:8]}...")
                                            if asyncio.iscoroutinefunction(callback):
                                                await callback(payment)
                                            else:
                                                # Run synchronous callback in thread pool to avoid blocking
                                                loop = asyncio.get_event_loop()
                                                await loop.run_in_executor(None, callback, payment)
                                        except Exception as e:
                                            logger.error(f"Error in callback function for payment {payment_id[:8]}...: {str(e)}", exc_info=True)
                                    
                                    # Create task for callback execution (non-blocking)
                                    callback_task = asyncio.create_task(run_callback())
                                    self._callback_tasks.add(callback_task)
                                    
                                    # Remove task from tracking when it completes
                                    def remove_callback_task(task):
                                        self._callback_tasks.discard(task)
                                    callback_task.add_done_callback(remove_callback_task)
                            
                            # Remove from tracking when payment is actually complete
                            # This happens after the callback has processed the payment and submitted results
                            # Stop checking when result is submitted or payment reaches final withdrawal states
                            if (on_chain_state in [
                                PaymentOnChainState.RESULT_SUBMITTED.value

                            ] or
                                next_action == PaymentNextAction.NONE.value):
                                
                                logger.info(f"Payment {payment_id[:8]}... is complete, removing from tracking")
                                payments_to_remove.append(payment_id)
                                # Clean up tracking
                                self._callback_triggered_ids.discard(payment_id)
                                payment_check_times.pop(payment_id, None)
                        
                        except Exception as e:
                            logger.error(f"Error checking status for payment {payment_id[:8]}...: {str(e)}")
                            failed_checks += 1
                            # Continue checking other payments even if one fails
                            continue
                    
                    # Remove completed payments
                    for payment_id in payments_to_remove:
                        self.payment_ids.discard(payment_id)
                    
                    if successful_checks > 0 or failed_checks > 0:
                        logger.debug(f"Granular check completed: {successful_checks} successful, {failed_checks} failed, {len(self.payment_ids)} active")
                
                    # If no more payments to monitor, exit the loop
                    if not self.payment_ids:
                        logger.info("No more payments to monitor, stopping monitoring task")
                        return
                    
                    # Short sleep before next check cycle (payments are checked individually based on their last check time)
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error during status monitoring: {str(e)}", exc_info=True)
                    await asyncio.sleep(interval_seconds)
        
        # Create and store the monitoring task
        self._status_check_task = asyncio.create_task(monitor_task())
        logger.debug("Monitoring task created and started")

    def stop_status_monitoring(self) -> None:
        """
        Stop the payment status monitoring.
        
        Cancels the monitoring task if it's running.
        Also cancels any pending callback tasks to prevent memory leaks.
        """
        if self._status_check_task:
            logger.info("Stopping payment status monitoring")
            self._status_check_task.cancel()
            self._status_check_task = None
            # Clean up callback tracking
            self._callback_triggered_ids.clear()
        
        # Cancel any pending callback tasks
        if self._callback_tasks:
            logger.debug(f"Cancelling {len(self._callback_tasks)} pending callback tasks")
            for task in self._callback_tasks.copy():
                if not task.done():
                    task.cancel()
            self._callback_tasks.clear()
        
        if not self._status_check_task and not self._callback_tasks:
            logger.debug("No monitoring task to stop")

    async def check_purchase_status(self, purchase_id: str) -> Dict:
        """Check the status of a purchase request"""
        logger.info(f"Checking status for purchase with ID: {purchase_id}")
        
        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{self.config.payment_service_url}/purchase/{purchase_id}",
                    headers=self._headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Purchase status check failed: {error_text}")
                        raise ValueError(f"Purchase status check failed: {error_text}")
                    
                    result = await response.json()
                    logger.info("Purchase status check completed successfully")
                    logger.debug(f"Purchase status response: {result}")
                    return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during purchase status check: {str(e)}")
            raise 
    
    async def authorize_refund(self, blockchain_identifier: str) -> Dict:
        """
        Authorize a refund request for a payment.
        
        This method allows the seller to authorize a refund that was requested by the buyer.
        
        Args:
            blockchain_identifier (str): The blockchain identifier of the payment
            
        Returns:
            dict: Response containing the updated payment information with refund authorization
        """
        logger.info(f"Authorizing refund for payment {blockchain_identifier}")
        
        payload = {
            "network": self.network,
            "blockchainIdentifier": blockchain_identifier
        }
        
        logger.debug(f"Authorize refund payload: {payload}")
        
        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    f"{self.config.payment_service_url}/payment/authorize-refund",
                    headers=self._headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Authorize refund failed: {error_text}")
                        raise ValueError(f"Authorize refund failed: {error_text}")
                    
                    result = await response.json()
                    logger.info("Refund authorized successfully")
                    logger.debug(f"Authorize refund response: {result}")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during refund authorization: {str(e)}")
            raise
