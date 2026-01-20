"""
Endpoint handler abstractions for MIP-003 agent API endpoints.
"""

import logging
from typing import Optional, Callable, Dict, Any, Awaitable, Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class AgentEndpointHandler:
    """Main class that manages endpoint callbacks for MIP-003 endpoints."""
    
    def __init__(self):
        """Initialize the endpoint handler with no callbacks set."""
        self._start_job_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None
        self._status_handler: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None
        self._availability_handler: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None
        self._input_schema: Optional[Union[Dict[str, Any], Callable[[], Dict[str, Any]]]] = None
        self._provide_input_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None
        self._demo_handler: Optional[Callable[[], Dict[str, Any]]] = None
        logger.info("Initialized AgentEndpointHandler")
    
    def start_job(self, func: Callable[[str, Dict[str, Any]], Awaitable[Any]]):
        """
        Decorator for /start_job endpoint handler.
        
        The handler function should accept:
        - identifier_from_purchaser: str
        - input_data: Dict[str, Any]
        
        And return the job result (can be string, dict, or any serializable type).
        """
        self._start_job_handler = func
        logger.info(f"Registered start_job handler: {func.__name__}")
        return func
    
    def status(self, func: Callable[[str], Awaitable[Dict[str, Any]]]):
        """
        Decorator for /status endpoint handler.
        
        The handler function should accept:
        - job_id: str
        
        And return a dict with job status information.
        """
        self._status_handler = func
        logger.info(f"Registered status handler: {func.__name__}")
        return func
    
    def availability(self, func: Callable[[], Awaitable[Dict[str, Any]]]):
        """
        Decorator for /availability endpoint handler.
        
        The handler function should accept no arguments and return a dict with:
        - status: str (e.g., "available" or "unavailable")
        - type: str (e.g., "masumi-agent")
        - message: Optional[str]
        """
        self._availability_handler = func
        logger.info(f"Registered availability handler: {func.__name__}")
        return func
    
    def input_schema(self, schema: Union[Dict[str, Any], Callable[[], Dict[str, Any]]]):
        """
        Decorator for /input_schema endpoint handler.
        
        Accepts either:
        - A dict (static schema) - RECOMMENDED: Most agents use static schemas
        - A callable that returns a dict (dynamic schema) - OPTIONAL: For cases where schema
          needs to change based on context (e.g., user permissions, configuration, time)
        
        The schema should be a dict with:
        - input_data: List[InputField] (optional)
        - input_groups: List[InputGroup] (optional)
        """
        self._input_schema = schema
        if callable(schema):
            logger.info(f"Registered input_schema handler (dynamic): {schema.__name__ if hasattr(schema, '__name__') else 'anonymous'}")
        else:
            logger.info("Registered input_schema (static)")
        return schema
    
    def provide_input(self, func: Callable[[str, Dict[str, Any]], Awaitable[Any]]):
        """
        Decorator for /provide_input endpoint handler (optional).
        
        The handler function should accept:
        - job_id: str
        - input_data: Dict[str, Any]
        """
        self._provide_input_handler = func
        logger.info(f"Registered provide_input handler: {func.__name__}")
        return func
    
    def demo(self, func: Callable[[], Dict[str, Any]]):
        """
        Decorator for /demo endpoint handler (optional).
        
        The handler function should accept no arguments and return a dict with:
        - input: Dict[str, Any] (example input)
        - output: Dict[str, str] (example output)
        """
        self._demo_handler = func
        logger.info(f"Registered demo handler: {func.__name__}")
        return func
    
    # Getter methods for accessing handlers
    def get_start_job_handler(self) -> Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]]:
        """Get the start_job handler."""
        return self._start_job_handler
    
    def get_status_handler(self) -> Optional[Callable[[str], Awaitable[Dict[str, Any]]]]:
        """Get the status handler."""
        return self._status_handler
    
    def get_availability_handler(self) -> Optional[Callable[[], Awaitable[Dict[str, Any]]]]:
        """Get the availability handler."""
        return self._availability_handler
    
    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the input schema.
        
        Returns the schema dict, whether it's stored as a dict or callable.
        If it's a callable, it will be called to get the current schema.
        
        Returns:
            The input schema dict, or None if not set
        """
        if self._input_schema is None:
            return None
        if callable(self._input_schema):
            return self._input_schema()
        return self._input_schema
    
    def get_provide_input_handler(self) -> Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]]:
        """Get the provide_input handler."""
        return self._provide_input_handler
    
    def get_demo_handler(self) -> Optional[Callable[[], Dict[str, Any]]]:
        """Get the demo handler."""
        return self._demo_handler
    
    def set_start_job_handler(self, handler: Callable[[str, Dict[str, Any]], Awaitable[Any]]):
        """Set the start_job handler directly (non-decorator method)."""
        self._start_job_handler = handler
        logger.info(f"Set start_job handler: {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'}")
    
    def set_status_handler(self, handler: Callable[[str], Awaitable[Dict[str, Any]]]):
        """Set the status handler directly (non-decorator method)."""
        self._status_handler = handler
        logger.info(f"Set status handler: {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'}")
    
    def set_availability_handler(self, handler: Callable[[], Awaitable[Dict[str, Any]]]):
        """Set the availability handler directly (non-decorator method)."""
        self._availability_handler = handler
        logger.info(f"Set availability handler: {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'}")
    
    def set_input_schema_handler(self, schema: Union[Dict[str, Any], Callable[[], Dict[str, Any]]]):
        """
        Set the input_schema directly (non-decorator method).
        
        Args:
            schema: The input schema dict (RECOMMENDED) or a callable that returns a dict (OPTIONAL)
                   Static schemas (dict) are the default and recommended for most agents.
                   Dynamic schemas (callable) are available for cases where the schema needs to
                   change based on context (e.g., user permissions, configuration, time).
        """
        self._input_schema = schema
        if callable(schema):
            logger.info(f"Set input_schema handler (dynamic): {schema.__name__ if hasattr(schema, '__name__') else 'anonymous'}")
        else:
            logger.info("Set input_schema (static)")
    
    def set_provide_input_handler(self, handler: Callable[[str, Dict[str, Any]], Awaitable[Any]]):
        """Set the provide_input handler directly (non-decorator method)."""
        self._provide_input_handler = handler
        logger.info(f"Set provide_input handler: {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'}")
    
    def set_demo_handler(self, handler: Callable[[], Dict[str, Any]]):
        """Set the demo handler directly (non-decorator method)."""
        self._demo_handler = handler
        logger.info(f"Set demo handler: {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'}")

