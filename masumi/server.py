"""
FastAPI server framework for MIP-003 agent endpoints.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Optional, Callable, Dict, Any, Awaitable, Union, Set
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import Config
from .payment import Payment
from .models import (
    StartJobRequest,
    StartJobResponse,
    StatusResponse,
    AvailabilityResponse,
    InputSchemaResponse,
    ProvideInputRequest,
    ProvideInputResponse,
    DemoResponse
)
from .endpoints import AgentEndpointHandler
from .job_manager import JobManager, JobStorage, InMemoryJobStorage
from .validation import validate_input_data, ValidationError
from .helper_functions import setup_logging, create_masumi_input_hash, check_free_agent_from_registry
from .models import JobStatus
from .hitl import set_job_context, clear_job_context, provide_input_to_job

logger = setup_logging(__name__)


class MasumiAgentServer:
    """FastAPI server that handles all MIP-003 endpoints."""
    
    def __init__(
        self,
        config: Config,
        agent_identifier: Optional[str] = None,
        network: str = "Preprod",
        job_storage: Optional[JobStorage] = None,
        start_job_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None,
        input_schema_handler: Optional[Union[Dict[str, Any], Callable[[], Dict[str, Any]]]] = None,
        status_handler: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None,
        availability_handler: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
        provide_input_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None,
        demo_handler: Optional[Callable[[], Dict[str, Any]]] = None,
        seller_vkey: Optional[str] = None
    ):
        """
        Initialize the Masumi agent server.
        
        Args:
            config: Configuration with API endpoints and keys
            agent_identifier: Agent identifier from admin interface (OPTIONAL for API mode).
                              Can be provided directly or via AGENT_IDENTIFIER environment variable.
                              If not provided, the server will start with a warning and use a placeholder identifier.
            network: Network to use (Preprod or Mainnet)
            job_storage: Optional custom job storage backend
            start_job_handler: Handler for executing agent logic
            input_schema_handler: Input schema dict (RECOMMENDED) or callable that returns dict (OPTIONAL).
                                  Static schemas (dict) are the default and recommended for most agents.
                                  Dynamic schemas (callable) are available for cases where the schema needs
                                  to change based on context (e.g., user permissions, configuration, time).
            status_handler: Optional custom status handler
            availability_handler: Optional custom availability handler
            provide_input_handler: Optional handler for provide_input endpoint
            demo_handler: Optional handler for demo endpoint
            seller_vkey: Optional seller wallet vkey (if not provided, will be loaded from SELLER_VKEY environment variable)
        
        Raises:
            ValueError: If seller_vkey is not provided (either directly or via SELLER_VKEY env var).
                        Note: agent_identifier is optional - if not provided, a warning will be logged and
                        a placeholder identifier will be used.
        """
        import os
        
        # Load agent_identifier from environment if not provided
        if not agent_identifier:
            agent_identifier = os.getenv("AGENT_IDENTIFIER")
        
        # Warn if agent_identifier is not provided, but allow server to start
        if not agent_identifier:
            logger.warning(
                "AGENT_IDENTIFIER is not set. The agent will run but may have limited functionality. "
                "Set AGENT_IDENTIFIER environment variable or provide it directly. "
                "Get your agent_identifier from the admin interface after registering your agent."
            )
            # Use a placeholder for agent_identifier to allow server to start
            agent_identifier = "unregistered-agent"
        
        # Load seller_vkey from environment if not provided
        if not seller_vkey:
            seller_vkey = os.getenv("SELLER_VKEY")

        # Note: seller_vkey validation moved to /start_job endpoint after registry check
        # (registry determines if agent is free; free agents don't need seller_vkey)
        if not seller_vkey:
            seller_vkey = ""  # Will be validated in start_job if not a free agent
        
        self.config = config
        self.agent_identifier = agent_identifier
        self.network = network
        self.seller_vkey = seller_vkey
        
        # Track background tasks to prevent memory leaks
        self._background_tasks: Set[asyncio.Task] = set()
        
        # Initialize job manager with storage
        storage = job_storage or InMemoryJobStorage()
        self.job_manager = JobManager(storage)
        
        # Initialize endpoint handler
        self.handler = AgentEndpointHandler()
        
        # Set handlers if provided
        if start_job_handler:
            self.handler.set_start_job_handler(start_job_handler)
        if input_schema_handler:
            self.handler.set_input_schema_handler(input_schema_handler)
        if status_handler:
            self.handler.set_status_handler(status_handler)
        if availability_handler:
            self.handler.set_availability_handler(availability_handler)
        if provide_input_handler:
            self.handler.set_provide_input_handler(provide_input_handler)
        if demo_handler:
            self.handler.set_demo_handler(demo_handler)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Masumi Agent API",
            description="MIP-003 compliant agent API with Masumi payment integration",
            version="1.0.0"
        )
        
        # Register shutdown handler to clean up background tasks
        @self.app.on_event("shutdown")
        async def shutdown_handler():
            await self.cleanup_background_tasks()

        # Log 422 validation errors for debugging (e.g. Sokosumi request format)
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            body = b""
            try:
                body = await request.body()
            except Exception:
                pass
            logger.warning(
                f"Request validation failed (422) for {request.url.path}: "
                f"errors={exc.errors()}, body={body.decode('utf-8', errors='replace')[:500]}"
            )
            return JSONResponse(status_code=422, content={"detail": exc.errors()})
        
        # Register all endpoints
        self._register_endpoints()
        
        logger.info(f"Initialized MasumiAgentServer for agent {agent_identifier} on {network} network")
    
    def _register_endpoints(self):
        """Register all MIP-003 endpoints."""
        
        @self.app.post("/start_job", response_model=StartJobResponse)
        async def start_job(request: StartJobRequest):  # noqa: F841
            """MIP-003: /start_job - Initiates a job and creates a payment request"""
            try:
                # Validate input data if schema is provided
                schema = self.handler.get_input_schema()
                if schema:
                    try:
                        validate_input_data(request.input_data or {}, schema)
                    except ValidationError as e:
                        # Log validation error with context for admin interface
                        logger.warning(
                            f"Input validation failed for agent {self.agent_identifier}: {str(e)}. "
                            f"Request from purchaser: {request.identifier_from_purchaser[:8] if request.identifier_from_purchaser else 'unknown'}... "
                            f"Field errors: {getattr(e, 'field_errors', {})}"
                        )
                        # Return structured error information useful for admin interface
                        error_detail = {
                            "message": str(e),
                            "field_errors": getattr(e, 'field_errors', {})
                        }
                        raise HTTPException(status_code=400, detail=error_detail)
                    except Exception as e:
                        logger.warning(f"Error validating input: {e}")
                
                # Check that start_job_handler is set
                start_handler = self.handler.get_start_job_handler()
                if not start_handler:
                    raise HTTPException(
                        status_code=500,
                        detail="Start job handler not configured"
                    )

                # Check if this is a free agent by querying the registry
                is_free_agent = await check_free_agent_from_registry(
                    agent_identifier=self.agent_identifier,
                    payment_service_url=self.config.payment_service_url,
                    payment_api_key=self.config.payment_api_key,
                    network=self.network
                )

                # Validate seller_vkey for paid agents
                if not is_free_agent and not self.seller_vkey:
                    raise HTTPException(
                        status_code=500,
                        detail="seller_vkey is required for paid agents. Set SELLER_VKEY environment variable or provide it when creating the server."
                    )

                # Create payment request or mock for free agent
                payment = Payment(
                    agent_identifier=self.agent_identifier,
                    config=self.config,
                    identifier_from_purchaser=request.identifier_from_purchaser,
                    input_data=request.input_data,
                    network=self.network
                )

                if is_free_agent:
                    logger.info("Free agent detected - bypassing payment service")
                    # Create mock payment response without hitting payment service
                    payment_request = await payment.create_free_agent_mock_payment()
                    blockchain_identifier = payment_request["data"]["blockchainIdentifier"]
                else:
                    logger.info("Creating payment request...")
                    payment_request = await payment.create_payment_request()
                    blockchain_identifier = payment_request["data"]["blockchainIdentifier"]
                    payment.payment_ids.add(blockchain_identifier)
                
                # Get seller vkey (use provided or from env/config)
                seller_vkey = self.seller_vkey or payment_request["data"].get("sellerVKey", "")
                
                # Create job in job manager
                job_id = await self.job_manager.create_job(
                    identifier_from_purchaser=request.identifier_from_purchaser,
                    input_data=request.input_data or {},
                    payment=payment,
                    blockchain_identifier=blockchain_identifier,
                    pay_by_time=int(payment_request["data"]["payByTime"]),
                    submit_result_time=int(payment_request["data"]["submitResultTime"]),
                    unlock_time=int(payment_request["data"]["unlockTime"]),
                    external_dispute_unlock_time=int(payment_request["data"]["externalDisputeUnlockTime"]),
                    agent_identifier=self.agent_identifier,
                    seller_vkey=seller_vkey,
                    input_hash=payment.input_hash
                )

                if is_free_agent:
                    # For free agents, immediately trigger the job without waiting for payment
                    logger.info(f"Free agent job {job_id} - executing immediately without payment")
                    # Schedule the job execution in background; keep strong reference to prevent GC
                    task = asyncio.create_task(self._handle_payment_confirmed(job_id, blockchain_identifier))
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
                else:
                    # Set up payment callback for paid agents
                    # Callback receives the full payment dict (as per payment.py documentation)
                    async def payment_callback(payment: Dict[str, Any]):
                        payment_id = payment.get("blockchainIdentifier", "")
                        await self._handle_payment_confirmed(job_id, payment_id)

                    # Start monitoring payment
                    logger.info(f"Starting payment monitoring for job {job_id}")
                    await payment.start_status_monitoring(callback=payment_callback)
                
                # Return response
                return StartJobResponse(
                    id=job_id,
                    blockchainIdentifier=blockchain_identifier,
                    payByTime=int(payment_request["data"]["payByTime"]),
                    submitResultTime=int(payment_request["data"]["submitResultTime"]),
                    unlockTime=int(payment_request["data"]["unlockTime"]),
                    externalDisputeUnlockTime=int(payment_request["data"]["externalDisputeUnlockTime"]),
                    agentIdentifier=self.agent_identifier,
                    sellerVKey=seller_vkey,
                    identifierFromPurchaser=request.identifier_from_purchaser,
                    input_hash=payment.input_hash or ""
                )
                
            except HTTPException:
                raise
            except KeyError as e:
                logger.error(f"Missing required field: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail="Bad Request: If input_data or identifier_from_purchaser is missing, invalid, or does not adhere to the schema."
                )
            except Exception as e:
                logger.error(f"Error in start_job: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {str(e)}"
                )
        
        @self.app.get("/status", response_model=StatusResponse)
        async def get_status(
            jobId: Optional[str] = Query(None, alias="jobId", description="Job ID (MIP-003)"),
            job_id: Optional[str] = Query(None, alias="job_id", description="Job ID (legacy)"),
        ):
            """MIP-003: /status - Retrieves the current status of a specific job"""
            job_id_resolved = jobId or job_id
            if not job_id_resolved:
                raise HTTPException(
                    status_code=422,
                    detail="Missing required query parameter: jobId or job_id",
                )
            # Use custom handler if provided
            custom_handler = self.handler.get_status_handler()
            if custom_handler:
                try:
                    return await custom_handler(job_id_resolved)
                except Exception as e:
                    logger.error(f"Error in custom status handler: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail=str(e))
            
            # Default implementation
            job = await self.job_manager.get_job(job_id_resolved)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            status = job.get("status", JobStatus.UNKNOWN.value)
            result = job.get("result")
            # Result should already be a string (agents return strings)
            # Return None if result is not set yet
            result_string = result if isinstance(result, str) else None
            
            # Include input schema if awaiting input
            # Use the HITL-specific schema stored in the job, not the main input schema
            input_schema = None
            if status == JobStatus.AWAITING_INPUT.value:
                input_schema = job.get("awaiting_input_schema")
                # Fallback to main schema if HITL schema not found (shouldn't happen, but be safe)
                if not input_schema:
                    input_schema = self.handler.get_input_schema()
            
            return StatusResponse(
                id=str(uuid.uuid4()),
                status=status,
                input_schema=input_schema,
                result=result_string
            )
        
        @self.app.get("/availability", response_model=AvailabilityResponse)
        async def check_availability():
            """MIP-003: /availability - Checks if the server is operational"""
            custom_handler = self.handler.get_availability_handler()
            if custom_handler:
                try:
                    result = await custom_handler()
                    return AvailabilityResponse(**result)
                except Exception as e:
                    logger.error(f"Error in custom availability handler: {e}", exc_info=True)
            
            # Default implementation
            return AvailabilityResponse(
                status="available",
                type="masumi-agent",
                message="Server operational"
            )
        
        @self.app.get("/input_schema", response_model=InputSchemaResponse)
        async def input_schema():
            """MIP-003: /input_schema - Returns the expected input format for jobs"""
            schema = self.handler.get_input_schema()
            if not schema:
                raise HTTPException(
                    status_code=500,
                    detail="Input schema not configured"
                )
            
            try:
                return InputSchemaResponse(**schema)
            except Exception as e:
                logger.error(f"Error returning input_schema: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/provide_input", response_model=ProvideInputResponse)
        async def provide_input(request: ProvideInputRequest):
            """MIP-003: /provide_input - Provides additional input for a job awaiting input"""
            custom_handler = self.handler.get_provide_input_handler()
            
            try:
                # Use custom handler if provided, otherwise use default
                if custom_handler:
                    await custom_handler(request.job_id, request.input_data)
                else:
                    await self._default_provide_input_handler(request.job_id, request.input_data)
                
                # Always signal the waiting coroutine that input has arrived
                # This must happen regardless of which handler was used, otherwise
                # jobs using request_input() will hang indefinitely
                # Note: If a custom handler is used, we still need to signal the HITL event
                # because the custom handler cannot easily call provide_input_to_job itself
                if custom_handler:
                    provide_input_to_job(request.job_id, request.input_data)
                
                # Get job to retrieve identifier_from_purchaser for hash calculation
                job = await self.job_manager.get_job(request.job_id)
                if not job:
                    raise ValueError(f"Job {request.job_id} not found")
                
                # Calculate input_hash for the provided input_data
                identifier_from_purchaser = job.get("identifier_from_purchaser", "")
                input_hash = create_masumi_input_hash(request.input_data, identifier_from_purchaser)
                
                # Return response with input_hash and signature (signature is empty for now)
                return ProvideInputResponse(
                    input_hash=input_hash,
                    signature=""  # Signature not implemented yet, empty string for compatibility
                )
            except Exception as e:
                logger.error(f"Error in provide_input handler: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/demo", response_model=DemoResponse)
        async def demo():
            """MIP-003: /demo - Returns demo data for marketing purposes"""
            handler = self.handler.get_demo_handler()
            if not handler:
                raise HTTPException(
                    status_code=501,
                    detail="Demo endpoint not implemented"
                )
            
            try:
                demo_data = handler()
                return DemoResponse(**demo_data)
            except Exception as e:
                logger.error(f"Error in demo handler: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _handle_payment_confirmed(self, job_id: str, payment_id: str):
        """Handle payment confirmation - start background task for agent logic."""
        try:
            logger.info(f"Payment {payment_id[:8]}... confirmed for job {job_id}, starting agent logic...")
            
            # Update job status to running
            await self.job_manager.set_job_running(job_id)
            
            # Start actual job execution in a background task
            # This ensures that the payment monitoring loop is not blocked
            # and the server remains responsive to status requests
            task = asyncio.create_task(self._execute_agent_job(job_id))
            self._background_tasks.add(task)
            
            # Remove task from tracking when it completes
            task.add_done_callback(self._background_tasks.discard)
            
            logger.info(f"Agent logic task spawned for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error starting agent logic for job {job_id}: {e}", exc_info=True)
            try:
                await self.job_manager.set_job_failed(job_id, str(e))
                await self.job_manager.cleanup_payment_instance(job_id)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}", exc_info=True)

    async def _execute_agent_job(self, job_id: str):
        """Internal method to execute agent logic and handle results."""
        try:
            # Get job data
            job = await self.job_manager.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found during execution")
                return
            
            logger.info(f"Input data for job {job_id}: {job.get('input_data')}")
            
            # Get handler
            start_handler = self.handler.get_start_job_handler()
            if not start_handler:
                logger.error(f"Start job handler not configured for job {job_id}")
                await self.job_manager.set_job_failed(job_id, "Start job handler not configured")
                await self.job_manager.cleanup_payment_instance(job_id)
                return
            
            # Execute agent logic
            input_data = job.get("input_data", {})
            identifier_from_purchaser = job.get("identifier_from_purchaser", "")
            
            # Set job context for HITL functionality
            set_job_context(job_id, self.job_manager)
            try:
                try:
                    # We await the handler. If it's a long-running but properly async function,
                    # the event loop will remain responsive to other requests.
                    # If request_input() is called, it will pause execution here until input is provided.
                    result = await start_handler(identifier_from_purchaser, input_data)
                    logger.info(f"Agent logic completed for job {job_id}")
                finally:
                    # Always clear the context after execution
                    clear_job_context()
            except Exception as e:
                logger.error(f"Error executing agent logic for job {job_id}: {e}", exc_info=True)
                await self.job_manager.set_job_failed(job_id, str(e))
                await self.job_manager.cleanup_payment_instance(job_id)
                return
            
            # Ensure result is a string for on-chain hashing
            # Agents are expected to return strings - we only convert non-strings for compatibility
            if not isinstance(result, str):
                try:
                    logger.info(f"Converting {type(result).__name__} result to JSON string")
                    result = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    error_msg = f"Failed to serialize agent result: {str(e)}"
                    logger.error(f"Invalid result for job {job_id}: {error_msg}")
                    await self.job_manager.set_job_failed(job_id, error_msg)
                    await self.job_manager.cleanup_payment_instance(job_id)
                    return
            
            # Update job status to completed (now also handles on-chain submission)
            try:
                await self.job_manager.set_job_completed(job_id, result)
                logger.info(f"Job {job_id} successfully completed and result submitted.")
            except Exception as e:
                logger.error(f"Error completing job {job_id}: {e}", exc_info=True)
                await self.job_manager.set_job_failed(job_id, f"Job completion failed: {str(e)}")
                # We cleanup on failure because we won't be reaching a 'Complete' state normally
                await self.job_manager.cleanup_payment_instance(job_id)
                return
            
            # Free agents never start payment monitoring, so we must cleanup here.
            # Paid agents: monitoring task runs until on-chain confirmation; no cleanup needed here.
            payment_id = job.get("payment_id", "")
            if payment_id.startswith("FREE-"):
                await self.job_manager.cleanup_payment_instance(job_id)
                logger.info(f"Free agent job {job_id} finished; payment instance cleaned up.")
            else:
                logger.info(f"Job {job_id} logic finished. Monitoring will continue until on-chain confirmation.")
            
        except Exception as e:
            logger.error(f"Fatal error in _execute_agent_job for job {job_id}: {e}", exc_info=True)
            try:
                await self.job_manager.set_job_failed(job_id, str(e))
                await self.job_manager.cleanup_payment_instance(job_id)
            except Exception as cleanup_error:
                logger.error(f"Error during final cleanup: {cleanup_error}", exc_info=True)
    
    async def _default_provide_input_handler(self, job_id: str, input_data: Dict[str, Any]) -> None:
        """
        Default handler for /provide_input endpoint.
        
        This handler:
        1. Validates the job is in AWAITING_INPUT status
        2. Validates input data against the stored schema (if available)
        3. Resumes the job with the provided input
        4. Signals the waiting coroutine to continue execution
        
        Args:
            job_id: The job ID
            input_data: The input data provided by the human
        """
        # Get the job
        job = await self.job_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Verify job is awaiting input
        if job.get("status") != JobStatus.AWAITING_INPUT.value:
            raise ValueError(
                f"Job {job_id} is not awaiting input. Current status: {job.get('status')}"
            )
        
        # Validate input against schema if available
        input_schema = job.get("awaiting_input_schema")
        if input_schema:
            logger.debug(f"Validating input_data for job {job_id}: {input_data} against schema: {input_schema}")
            try:
                validate_input_data(input_data, input_schema)
            except ValidationError as e:
                # Provide more helpful error message
                schema_fields = []
                if "input_data" in input_schema:
                    schema_fields = [field.get("id", "unknown") for field in input_schema["input_data"]]
                elif "input_groups" in input_schema:
                    for group in input_schema["input_groups"]:
                        schema_fields.extend([field.get("id", "unknown") for field in group.get("input_data", [])])
                
                error_detail = {
                    "message": str(e),
                    "received_fields": list(input_data.keys()),
                    "expected_fields": schema_fields,
                    "field_errors": getattr(e, 'field_errors', {})
                }
                logger.warning(f"Input validation failed for job {job_id}: {error_detail}")
                raise ValueError(
                    f"Input validation failed: {str(e)}. "
                    f"Received fields: {list(input_data.keys())}, "
                    f"Expected fields: {schema_fields}"
                )
        
        # Resume the job with the input data
        # This merges the input_data with existing job input_data and sets status to RUNNING
        await self.job_manager.resume_job_with_input(job_id, input_data)
        
        # Signal the waiting coroutine that input has arrived
        provide_input_to_job(job_id, input_data)
        
        logger.info(f"Input provided for job {job_id}, resuming execution")
    
    async def cleanup_background_tasks(self):
        """Cancel all background tasks to prevent memory leaks on shutdown."""
        if self._background_tasks:
            logger.info(f"Cancelling {len(self._background_tasks)} background tasks")
            for task in self._background_tasks.copy():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.warning(f"Error cancelling background task: {e}")
            self._background_tasks.clear()
            logger.info("All background tasks cleaned up")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app
    
    # Decorator methods for easy handler registration
    def start_job(self, func: Callable[[str, Dict[str, Any]], Awaitable[Any]]):
        """Decorator for start_job handler."""
        self.handler.start_job(func)
        return func
    
    def status(self, func: Callable[[str], Awaitable[Dict[str, Any]]]):
        """Decorator for status handler."""
        self.handler.status(func)
        return func
    
    def availability(self, func: Callable[[], Awaitable[Dict[str, Any]]]):
        """Decorator for availability handler."""
        self.handler.availability(func)
        return func
    
    def input_schema(self, schema: Union[Dict[str, Any], Callable[[], Dict[str, Any]]]):
        """
        Decorator for input_schema.
        
        Accepts either:
        - A dict (static schema) - RECOMMENDED: Most agents use static schemas
        - A callable that returns a dict (dynamic schema) - OPTIONAL: For cases where schema
          needs to change based on context (e.g., user permissions, configuration, time)
        """
        self.handler.input_schema(schema)
        return schema
    
    def provide_input(self, func: Callable[[str, Dict[str, Any]], Awaitable[Any]]):
        """Decorator for provide_input handler."""
        self.handler.provide_input(func)
        return func
    
    def demo(self, func: Callable[[], Dict[str, Any]]):
        """Decorator for demo handler."""
        self.handler.demo(func)
        return func


def create_masumi_app(
    config: Config,
    agent_identifier: Optional[str] = None,
    network: str = "Preprod",
    job_storage: Optional[JobStorage] = None,
    start_job_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None,
    input_schema_handler: Optional[Union[Dict[str, Any], Callable[[], Dict[str, Any]]]] = None,
    status_handler: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None,
    availability_handler: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
    provide_input_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None,
    demo_handler: Optional[Callable[[], Dict[str, Any]]] = None,
    seller_vkey: Optional[str] = None
) -> FastAPI:
    """
    Helper function to create a FastAPI app with all MIP-003 endpoints.
    
    Args:
        config: Configuration with API endpoints and keys
        agent_identifier: Agent identifier from admin interface (OPTIONAL for API mode).
                          Can be provided directly or via AGENT_IDENTIFIER environment variable.
                          If not provided, the server will start with a warning and use a placeholder identifier.
        network: Network to use (Preprod or Mainnet)
        job_storage: Optional custom job storage backend
        start_job_handler: Handler for executing agent logic (required)
        input_schema_handler: Input schema dict (RECOMMENDED) or callable that returns dict (OPTIONAL).
                              Static schemas (dict) are the default and recommended for most agents.
                              Dynamic schemas (callable) are available for cases where the schema needs
                              to change based on context (e.g., user permissions, configuration, time).
        status_handler: Optional custom status handler
        availability_handler: Optional custom availability handler
        provide_input_handler: Optional handler for provide_input endpoint
        demo_handler: Optional handler for demo endpoint
        seller_vkey: Optional seller wallet vkey
    
    Returns:
        FastAPI: Configured FastAPI application
    
    Note:
        agent_identifier is optional - if not provided, a warning will be logged and a placeholder
        identifier will be used. The server will still start successfully.
    """
    server = MasumiAgentServer(
        config=config,
        agent_identifier=agent_identifier,
        network=network,
        job_storage=job_storage,
        start_job_handler=start_job_handler,
        input_schema_handler=input_schema_handler,
        status_handler=status_handler,
        availability_handler=availability_handler,
        provide_input_handler=provide_input_handler,
        demo_handler=demo_handler,
        seller_vkey=seller_vkey
    )
    return server.get_app()
