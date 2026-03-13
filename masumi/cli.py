"""
CLI module for Masumi agent execution and initialization.
"""

import os
import sys
import json
import asyncio
import logging
import importlib.util
import importlib
from typing import Optional, Callable, Dict, Any, Awaitable, Union
import uvicorn

from .config import Config
from .server import MasumiAgentServer, create_masumi_app
from .helper_functions import setup_logging, ColoredFormatter

logger = setup_logging(__name__)


def _configure_uvicorn_logging():
    """Configure uvicorn loggers to use our beautiful formatter and prevent duplication."""
    # Get uvicorn loggers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_error = logging.getLogger("uvicorn.error")
    
    # Remove all existing handlers to prevent duplication
    for log in [uvicorn_logger, uvicorn_access, uvicorn_error]:
        # Clear all handlers
        while log.handlers:
            log.removeHandler(log.handlers[0])
        # Prevent propagation to root logger to avoid duplicate messages
        log.propagate = False
    
    # Create a single shared handler with our formatter
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(use_colors=True, use_emojis=True)
    handler.setFormatter(formatter)
    
    # Set levels
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_access.setLevel(logging.WARNING)  # Suppress verbose HTTP access logs
    uvicorn_error.setLevel(logging.INFO)
    
    # Add handler to each logger
    uvicorn_logger.addHandler(handler)
    uvicorn_access.addHandler(handler)
    uvicorn_error.addHandler(handler)
    
    # Configure root logger to prevent duplicate messages
    # Only modify if it has basicConfig-style handlers
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for h in root_logger.handlers[:]:
            # Remove basic StreamHandlers that might cause duplication
            # Keep FileHandlers and other custom handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
                # Check if it's a default handler (no formatter or basic formatter)
                if h.formatter is None or (isinstance(h.formatter, logging.Formatter) and 
                                          h.formatter._fmt == logging.BASIC_FORMAT):
                    root_logger.removeHandler(h)


def _load_dotenv_if_available():
    """Load .env file as a fallback (main.py should load it, but this ensures compatibility)."""
    try:
        from dotenv import load_dotenv
        # Simple call - load_dotenv() searches from current directory upward automatically
        load_dotenv()
    except ImportError:
        # python-dotenv is optional - if not installed, that's okay
        # (user should install it if they want .env file support)
        pass


def run(
    start_job_handler: Callable[[str, Dict[str, Any]], Awaitable[Any]],
    input_schema_handler: Union[Dict[str, Any], Callable[[], Dict[str, Any]]],
    config: Optional[Config] = None,
    agent_identifier: Optional[str] = None,
    network: Optional[str] = None,
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    **kwargs
) -> None:
    """
    Run the Masumi agent in API mode (default).
    
    This function creates and runs a FastAPI server with Masumi payment integration.
    For standalone mode, use the CLI with --standalone flag.
    
    Args:
        start_job_handler: Handler function for executing agent logic
        input_schema_handler: Input schema dict or callable that returns dict
        config: Optional Config object (if None, created from environment variables)
        agent_identifier: Optional agent identifier (if None, read from AGENT_IDENTIFIER env var)
        network: Optional network name (if None, read from NETWORK env var or defaults to "Preprod")
        host: Host to bind to (default: "0.0.0.0")
        port: Port to bind to (if None, read from PORT env var or defaults to 8080)
        **kwargs: Additional arguments passed to MasumiAgentServer
    """
    # Load .env file if available (optional dependency)
    _load_dotenv_if_available()
    
    # Check if standalone mode is requested via environment variable
    if os.getenv("MASUMI_STANDALONE") == "1":
        # Standalone mode - execute handler directly
        _run_standalone(start_job_handler, input_schema_handler)
        return
    
    # API mode - create and run FastAPI server
    # Load config from environment if not provided
    if config is None:
        config = Config(
            payment_service_url=os.getenv(
                "PAYMENT_SERVICE_URL",
                "https://payment.masumi.network/api/v1"
            ),
            payment_api_key=os.getenv("PAYMENT_API_KEY", ""),
            free_agent=False  # Will be determined by registry check
        )
    
    # Load agent_identifier from environment if not provided
    if agent_identifier is None:
        agent_identifier = os.getenv("AGENT_IDENTIFIER")
    
    # Load network from environment if not provided
    if network is None:
        network = os.getenv("NETWORK", "Preprod")

    # Load port from environment if not provided
    if port is None:
        env_port = os.getenv("PORT")
        if env_port:
            try:
                port = int(env_port)
            except ValueError:
                logger.warning(f"Invalid PORT environment variable: {env_port}. Using default 8080.")
                port = 8080
        else:
            port = 8080
    
    # Load seller_vkey from environment if not provided in kwargs
    if "seller_vkey" not in kwargs:
        seller_vkey = os.getenv("SELLER_VKEY")
        if seller_vkey:
            kwargs["seller_vkey"] = seller_vkey
    
    # Create FastAPI app
    app = create_masumi_app(
        config=config,
        agent_identifier=agent_identifier,
        network=network,
        start_job_handler=start_job_handler,
        input_schema_handler=input_schema_handler,
        **kwargs
    )
    
    # Configure uvicorn logging to use our beautiful formatter
    _configure_uvicorn_logging()
    
    # Display startup information
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print("\n" + "=" * 70)
    print("🚀 Starting Masumi Agent Server...")
    print("=" * 70)
    print(f"API Documentation:        http://{display_host}:{port}/docs")
    print(f"Availability Check:       http://{display_host}:{port}/availability")
    print(f"Input Schema:             http://{display_host}:{port}/input_schema")
    print(f"Start Job:                http://{display_host}:{port}/start_job")
    print("=" * 70 + "\n")
    
    # Run server with cleaner logging
    # Using log_config=None prevents uvicorn from adding default handlers
    # Our _configure_uvicorn_logging() has already set up the handlers
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level="info",
        log_config=None  # Use our custom logging config (already configured above)
    )


def _run_standalone(
    start_job_handler: Callable[[str, Dict[str, Any]], Awaitable[Any]],
    input_schema_handler: Union[Dict[str, Any], Callable[[], Dict[str, Any]]],
    input_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Run agent in standalone mode - execute handler directly without API server.
    
    Args:
        start_job_handler: Handler function for executing agent logic
        input_schema_handler: Input schema dict or callable that returns dict
        input_data: Optional input data (if None, uses defaults from schema or empty dict)
    """
    print("\n" + "=" * 70)
    print("Running Agent Locally (Standalone Mode)")
    print("=" * 70)
    
    # Get input data
    if input_data is None:
        # Try to get default input from environment
        input_data_str = os.getenv("MASUMI_INPUT_DATA")
        if input_data_str:
            try:
                input_data = json.loads(input_data_str)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in MASUMI_INPUT_DATA: {input_data_str}")
                input_data = {}
        else:
            input_data = {}
    
    # Get schema to understand expected input
    if callable(input_schema_handler):
        schema = input_schema_handler()
    else:
        schema = input_schema_handler
    
    # Use test identifier for standalone mode
    identifier_from_purchaser = os.getenv("MASUMI_TEST_IDENTIFIER", "local_test_user")
    
    print(f"\nExecuting agent with input:")
    print(f"  Identifier: {identifier_from_purchaser}")
    print(f"  Input data: {json.dumps(input_data, indent=2)}")
    print("\n" + "-" * 70)
    
    # Execute handler
    try:
        result = asyncio.run(start_job_handler(identifier_from_purchaser, input_data))
        print("\n✅ Agent execution completed!")
        print(f"\nResult:")
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"  {result}")
    except Exception as e:
        print(f"\n❌ Error executing agent: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70 + "\n")


def _load_module_from_file(file_path: str):
    """Load a Python module from a file path."""
    # Add the directory containing the file to sys.path so imports work
    file_dir = os.path.dirname(os.path.abspath(file_path))
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)
    
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _extract_handlers_from_module(module):
    """Extract start_job_handler and input_schema_handler from a module."""
    start_job_handler = None
    input_schema_handler = None
    
    # Look for common handler names
    handler_names = [
        "process_job", "start_job", "start_job_handler", 
        "job_handler", "agent_handler"
    ]
    
    for name in handler_names:
        if hasattr(module, name):
            attr = getattr(module, name)
            if callable(attr):
                start_job_handler = attr
                break
    
    # Look for schema
    schema_names = ["INPUT_SCHEMA", "input_schema", "get_input_schema", "input_schema_handler"]
    for name in schema_names:
        if hasattr(module, name):
            attr = getattr(module, name)
            if isinstance(attr, dict) or callable(attr):
                input_schema_handler = attr
                break
    
    return start_job_handler, input_schema_handler


def run_command(args):
    """Handle the 'run' command."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Masumi Agent Builder CLI - Run Command")
        print("=" * 70)
        print("\nRun an agent file (API mode by default)")
        print("\nUsage:")
        print("  masumi run [file.py] [OPTIONS]")
        print("\nOptions:")
        print("  --standalone           Run in standalone mode (execute job directly)")
        print("  --input 'JSON'         Input data for standalone mode (JSON string)")
        print("  --help, -h             Show this help message")
        print("\nNote:")
        print("  If no file is provided, defaults to main.py")
        print("\nExecution Modes:")
        print("  API mode (default):")
        print("    Runs as FastAPI server with Masumi payment integration")
        print("    Requires: AGENT_IDENTIFIER (get it after registering your agent")
        print("              on the Masumi network), PAYMENT_API_KEY environment variables")
        print("\n  Standalone mode:")
        print("    Executes the agent function directly without API server")
        print("    Useful for local testing and development")
        print("\nExamples:")
        print("  masumi run                    # Runs main.py")
        print("  masumi run agent.py")
        print("  masumi run agent.py --standalone")
        print("  masumi run agent.py --standalone --input '{\"text\": \"Hello\"}'")
        print("\n  # Or run directly with Python (API mode)")
        print("  python agent.py")
        sys.exit(0)
    
    # Load .env file if available (optional dependency)
    _load_dotenv_if_available()
    
    # Default to main.py if no file is provided
    # Filter out flags to find the file argument
    file_path = None
    for arg in args:
        if not arg.startswith("--") and not arg.startswith("-"):
            file_path = arg
            break
    
    if file_path is None:
        file_path = "main.py"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Parse flags
    standalone = "--standalone" in args
    input_data = None
    
    # Extract --input flag value
    if "--input" in args:
        input_idx = args.index("--input")
        if input_idx + 1 < len(args):
            input_str = args[input_idx + 1]
            try:
                input_data = json.loads(input_str)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in --input: {input_str}")
                sys.exit(1)
    
    if standalone:
        # Standalone mode - import module and execute handler directly
        try:
            module = _load_module_from_file(file_path)
            start_job_handler, input_schema_handler = _extract_handlers_from_module(module)
            
            if start_job_handler is None:
                print("Error: Could not find start_job_handler in module.")
                print("Expected one of: process_job, start_job, start_job_handler, job_handler, agent_handler")
                sys.exit(1)
            
            if input_schema_handler is None:
                print("Error: Could not find input_schema_handler in module.")
                print("Expected one of: INPUT_SCHEMA, input_schema, get_input_schema, input_schema_handler")
                sys.exit(1)
            
            # Set environment variable for standalone mode
            os.environ["MASUMI_STANDALONE"] = "1"
            if input_data:
                os.environ["MASUMI_INPUT_DATA"] = json.dumps(input_data)
            
            # Execute standalone
            _run_standalone(start_job_handler, input_schema_handler, input_data)
        except Exception as e:
            print(f"Error running in standalone mode: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # API mode - execute the file normally (it should call masumi.run())
        try:
            # Set environment to indicate API mode
            os.environ.pop("MASUMI_STANDALONE", None)
            
            # Execute the file using subprocess to ensure proper module resolution
            # Set working directory to the file's directory so .env file can be found
            import subprocess
            file_dir = os.path.dirname(os.path.abspath(file_path))
            result = subprocess.run(
                [sys.executable, file_path],
                cwd=file_dir,
                check=False
            )
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Error running file: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def init_command(args):
    """Handle the 'init' command."""
    from .scaffold_templates import scaffold
    
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Masumi Agent Builder CLI - Init Command")
        print("=" * 70)
        print("\nGenerate a new Masumi agent project with full structure")
        print("\nUsage:")
        print("  masumi init [OPTIONS]")
        print("\nOptions:")
        print("  --name NAME            Project name (default: masumi-agent)")
        print("  --dir DIRECTORY        Output directory (default: project name)")
        print("  --non-interactive      Skip interactive prompts")
        print("  --help, -h             Show this help message")
        print("\nExamples:")
        print("  masumi init")
        print("  masumi init --name my-agent")
        print("  masumi init --dir my-project --non-interactive")
        sys.exit(0)
    
    # Parse arguments
    project_name = None
    output_dir = None
    interactive = True
    
    i = 0
    while i < len(args):
        if args[i] in ["--name", "--project-name"] and i + 1 < len(args):
            project_name = args[i + 1]
            i += 2
        elif args[i] in ["--dir", "--output-dir", "--directory"] and i + 1 < len(args):
            output_dir = args[i + 1]
            i += 2
        elif args[i] == "--non-interactive":
            interactive = False
            i += 1
        else:
            i += 1
    
    scaffold(
        project_name=project_name,
        output_dir=output_dir,
        interactive=interactive
    )


def check_command(args):
    """Handle the 'check' command."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Masumi Agent Builder CLI - Check Command")
        print("=" * 70)
        print("\nValidate your Masumi environment and configuration")
        print("\nUsage:")
        print("  masumi check [OPTIONS]")
        print("\nOptions:")
        print("  --verbose, -v          Show all checks (including passed)")
        print("\nThis command checks:")
        print("  - Python version (>= 3.8)")
        print("  - Virtual environment status")
        print("  - Required package installation")
        print("  - .env file existence")
        print("  - Environment variables (AGENT_IDENTIFIER, etc.)")
        print("  - Payment service connectivity")
        print("\nExamples:")
        print("  masumi check")
        print("  masumi check --verbose")
        sys.exit(0)

    # Parse flags
    verbose = "--verbose" in args or "-v" in args

    # Run the checker
    from .checker import run_check
    try:
        exit_code = asyncio.run(run_check(verbose=verbose))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running check: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def show_help():
    """Display comprehensive help information."""
    print("Masumi Agent Builder CLI")
    print("=" * 70)
    print("\nA command-line tool for building and running Masumi agents with")
    print("integrated payment processing.")
    print("\n" + "=" * 70)
    print("\nCOMMANDS")
    print("-" * 70)

    print("\n  init")
    print("    Generate a new Masumi agent project with full structure")
    print("\n    Usage:")
    print("      masumi init [OPTIONS]")
    print("\n    Options:")
    print("      --name NAME            Project name (default: masumi-agent)")
    print("      --dir DIRECTORY        Output directory (default: project name)")
    print("      --non-interactive      Skip interactive prompts")
    print("\n    Examples:")
    print("      masumi init")
    print("      masumi init --name my-agent")

    print("\n  run")
    print("    Run an agent file (API mode by default)")
    print("\n    Usage:")
    print("      masumi run [file.py] [OPTIONS]")
    print("\n    Options:")
    print("      --standalone           Run in standalone mode (execute job directly)")
    print("      --input 'JSON'         Input data for standalone mode (JSON string)")
    print("\n    Note:")
    print("      If no file is provided, defaults to main.py")
    print("\n    Examples:")
    print("      masumi run                    # Runs main.py")
    print("      masumi run agent.py")
    print("      masumi run agent.py --standalone")
    print("      masumi run agent.py --standalone --input '{\"text\": \"Hello\"}'")

    print("\n  check")
    print("    Validate your Masumi environment and configuration")
    print("\n    Usage:")
    print("      masumi check [OPTIONS]")
    print("\n    Options:")
    print("      --verbose, -v          Show all checks (including passed)")
    print("\n    Checks:")
    print("      - Python version (>= 3.8)")
    print("      - Virtual environment status")
    print("      - Required packages installation")
    print("      - Environment variables (AGENT_IDENTIFIER, PAYMENT_API_KEY, etc.)")
    print("      - Payment service connectivity")
    print("\n    Examples:")
    print("      masumi check                    # Quick check (only shows issues)")
    print("      masumi check --verbose          # Detailed check (shows everything)")

    print("\n" + "=" * 70)
    print("\nENVIRONMENT VARIABLES")
    print("-" * 70)
    print("\n  Required for API mode:")
    print("    AGENT_IDENTIFIER      Your agent ID (get it after registering your")
    print("                          agent on the Masumi network admin interface)")
    print("    PAYMENT_API_KEY       Your payment API key")
    print("\n  Optional:")
    print("    PAYMENT_SERVICE_URL   Payment service URL (defaults to production)")
    print("    NETWORK               Network: 'Preprod' or 'Mainnet' (defaults to 'Preprod')")
    print("    PORT                  Port to bind to (defaults to 8080)")
    print("\n  Note: Environment variables can be set in a .env file")
    print("        (.env files are automatically loaded)")
    
    print("\n" + "=" * 70)
    print("\nQUICK START")
    print("-" * 70)
    print("\n  1. Generate a new agent project:")
    print("     masumi init --name my-agent")
    print("\n  2. Set up the project:")
    print("     cd my-agent")
    print("     pip install -r requirements.txt")
    print("     cp .env.example .env")
    print("     # Edit .env with your values")
    print("\n  3. Register your agent on Masumi network and update .env:")
    print("     - AGENT_IDENTIFIER (get it after registration)")
    print("     - PAYMENT_API_KEY")
    print("     - SELLER_VKEY")
    print("\n  4. Validate your setup:")
    print("     masumi check")
    print("\n  5. Run your agent:")
    print("     masumi run agent.py")
    
    print("\n" + "=" * 70)
    print()


def main():
    """Main CLI entry point."""
    # Handle --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        show_help()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Masumi Agent Builder CLI")
        print("\nUsage:")
        print("  masumi init [--name NAME] [--dir DIR]")
        print("  masumi run [file.py] [--standalone] [--input 'JSON']")
        print("  masumi check")
        print("\nCommands:")
        print("  init      Generate a new Masumi agent project with full structure")
        print("  run       Run an agent file (defaults to main.py, API mode by default, use --standalone for direct execution)")
        print("  check     Validate your environment and configuration")
        print("\nUse 'masumi --help' for detailed information and all options.")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "init":
        init_command(args)
    elif command == "run":
        run_command(args)
    elif command == "check":
        check_command(args)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: init, run, check")
        print("Use 'masumi --help' for detailed information.")
        sys.exit(1)
