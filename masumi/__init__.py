"""
Masumi Payment Module for Cardano blockchain integration.
"""

import warnings

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional, but recommended
    pass

from .config import Config
from .payment import Payment, Amount
from .purchase import Purchase
from .helper_functions import create_masumi_input_hash, create_masumi_output_hash

# New endpoint abstraction exports
from .endpoints import AgentEndpointHandler
from .server import create_masumi_app, MasumiAgentServer
from .validation import validate_input_data, ValidationError
from .job_manager import JobManager, JobStorage, InMemoryJobStorage
from .cli import run
from .models import (
    StartJobRequest,
    StartJobResponse,
    StatusResponse,
    AvailabilityResponse,
    InputSchemaResponse,
    ProvideInputRequest,
    DemoResponse,
    InputField,
    InputGroup,
    ValidationRule
)

__version__ = "1.1.0"


class Agent:
    """
    DEPRECATED: The Agent class has been removed.
    
    Use `create_masumi_app()` or `MasumiAgentServer` instead.
    
    Migration guide:
    - Old: `agent = Agent(config, agent_id)`
    - New: `app = create_masumi_app(config=config, agent_identifier=agent_id, ...)`
    
    Or for more control:
    - New: `server = MasumiAgentServer(config=config, agent_identifier=agent_id, ...)`
    
    See README.md for examples and migration instructions.
    """
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "The Agent class has been removed. "
            "Use 'create_masumi_app()' or 'MasumiAgentServer' instead. "
            "See README.md for migration instructions.",
            DeprecationWarning,
            stacklevel=2
        )
        raise RuntimeError(
            "The Agent class has been removed. "
            "Please use 'create_masumi_app()' or 'MasumiAgentServer' instead. "
            "See README.md for examples and migration instructions."
        )

__all__ = [
    # Original exports (backward compatibility)
    "Config",
    "Payment", 
    "Amount",
    "Purchase",
    "create_masumi_input_hash",
    "create_masumi_output_hash",
    # New endpoint abstraction exports
    "AgentEndpointHandler",
    "create_masumi_app",
    "MasumiAgentServer",
    "validate_input_data",
    "ValidationError",
    "JobManager",
    "JobStorage",
    "InMemoryJobStorage",
    # Model exports
    "StartJobRequest",
    "StartJobResponse",
    "StatusResponse",
    "AvailabilityResponse",
    "InputSchemaResponse",
    "ProvideInputRequest",
    "DemoResponse",
    "InputField",
    "InputGroup",
    "ValidationRule",
    # CLI exports
    "run",
    # Deprecated (will warn on import/use)
    "Agent",
]
