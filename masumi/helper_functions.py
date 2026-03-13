import hashlib
import json
import canonicaljson
import logging as logger
import logging
import sys
import os
import aiohttp
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Beautiful colored formatter for Masumi logs."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Emojis for log levels
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    def __init__(self, use_colors=True, use_emojis=True, short_names=True):
        """
        Initialize the colored formatter.
        
        Args:
            use_colors: Whether to use ANSI colors (default: True, auto-detects TTY)
            use_emojis: Whether to use emojis for log levels (default: True)
            short_names: Whether to shorten module names (default: True)
        """
        # Auto-detect if colors should be used (check if output is a TTY)
        if use_colors and not hasattr(sys.stdout, 'isatty'):
            use_colors = False
        elif use_colors:
            use_colors = sys.stdout.isatty() and os.getenv('TERM') != 'dumb'
        
        self.use_colors = use_colors
        self.use_emojis = use_emojis
        self.short_names = short_names
        
        # Use a simpler format
        super().__init__()
    
    def format(self, record):
        """Format the log record with colors and emojis."""
        # Shorten module names (e.g., "masumi.server" -> "server")
        # Use a local variable to avoid modifying the original record
        display_name = record.name
        if self.short_names:
            name_parts = record.name.split('.')
            if len(name_parts) > 1 and name_parts[0] == 'masumi':
                display_name = '.'.join(name_parts[1:])
            elif len(name_parts) > 2:
                # For deeply nested modules, show last 2 parts
                display_name = '.'.join(name_parts[-2:])
        
        # Get level name and color
        levelname = record.levelname
        color = self.COLORS.get(levelname, '')
        emoji = self.EMOJIS.get(levelname, '') if self.use_emojis else ''
        
        # Build the formatted message
        if self.use_colors:
            level_str = f"{color}{self.BOLD}{levelname:8s}{self.RESET}"
            name_str = f"\033[90m{display_name}\033[0m"  # Dim gray for module name
        else:
            level_str = f"{levelname:8s}"
            name_str = display_name
        
        # Format: emoji LEVEL module: message
        # Use explicit spacing: space before emoji, two spaces after emoji for visual separation
        if emoji:
            formatted = " " + emoji + "  " + level_str + " " + name_str + ": " + record.getMessage()
        else:
            formatted = level_str + " " + name_str + ": " + record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        return formatted


def setup_logging(name, level=logging.INFO, use_colors=True, use_emojis=True):
    """
    Centralized logging configuration for Masumi modules.
    
    Configures a logger with a beautiful colored console handler if no handlers are present.
    This prevents duplicate handlers when the function is called multiple times.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (default: logging.INFO)
        use_colors: Whether to use colors (default: True, auto-detects TTY)
        use_emojis: Whether to use emojis for log levels (default: True)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(level)
    
    # Prevent propagation to parent loggers to avoid duplicate messages
    logger_instance.propagate = False
    
    if not logger_instance.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = ColoredFormatter(use_colors=use_colors, use_emojis=use_emojis)
        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)
    
    return logger_instance

def _create_hash_from_payload(payload_string: str, identifier_from_purchaser: str) -> str:
    """
    Internal core function that performs the standardized hashing.
    It takes the final, processed data payload string and the identifier.
    """
    # Steps 1.2, 2.2: Construct the pre-image with a semicolon delimiter.
    string_to_hash = f"{identifier_from_purchaser};{payload_string}"
    logger.debug(f"Pre-image for hashing: {string_to_hash}")

    # Steps 1.3, 2.3: Encode to UTF-8 and hash with SHA-256.
    return hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()

def create_masumi_input_hash(input_data: dict, identifier_from_purchaser: str) -> str:
    """
    Creates an input hash according to MIP-004.
    This function handles the specific pre-processing for input data (JCS).
    """
    # Step 1.1: Serialize the input dict using JCS (RFC 8785).
    canonical_input_json_string = canonicaljson.encode_canonical_json(input_data).decode('utf-8')
    logger.debug(f"Canonical Input JSON: {canonical_input_json_string}")

    # Call the core hashing function with the processed data.
    return _create_hash_from_payload(canonical_input_json_string, identifier_from_purchaser)

def create_masumi_output_hash(output_string: str, identifier_from_purchaser: str) -> str:
    """
    Creates an output hash according to MIP-004.
    This function uses the raw output string as the payload and applies
    JSON escaping to match the reference implementation.
    """
    if not isinstance(output_string, str):
        raise TypeError("output_string must be a string")

    # Step 2.1: Escape special characters in the result string using JSON encoding
    escaped_output = json.dumps(output_string, ensure_ascii=False)[1:-1]
    logger.info(f"Escaped Output for hashing: {escaped_output}")

    # Call the core hashing function with the processed data.
    result_hash = _create_hash_from_payload(escaped_output, identifier_from_purchaser)
    logger.info(f"Generated Output Hash: {result_hash}")
    return result_hash


async def check_free_agent_from_registry(
    agent_identifier: str,
    payment_service_url: Optional[str] = None,
    payment_api_key: Optional[str] = None,
    network: str = "Preprod"
) -> bool:
    """
    Query the registry to check if an agent is marked as free.

    Args:
        agent_identifier: The agent identifier to check
        payment_service_url: URL of the payment service (same service hosts registry endpoint)
        payment_api_key: API key for the service
        network: The Cardano network (Preprod or Mainnet)

    Returns:
        bool: True if the agent is marked as free, False otherwise

    Raises:
        Exception: If registry query fails
    """
    # Use default payment service URL if not provided
    if not payment_service_url:
        payment_service_url = os.getenv(
            "PAYMENT_SERVICE_URL",
            "https://payment.masumi.network/api/v1"
        )

    # Load API key from env if not provided
    if not payment_api_key:
        payment_api_key = os.getenv("PAYMENT_API_KEY", "")

    if not agent_identifier or agent_identifier == "unregistered-agent":
        # If agent is not registered, assume not free (default behavior)
        logging.warning(
            "Agent identifier not set or unregistered. Assuming non-free agent. "
            "Set AGENT_IDENTIFIER environment variable or register your agent."
        )
        return False

    # Check if API key is available
    if not payment_api_key:
        logging.error(
            "PAYMENT_API_KEY is not set. Cannot query registry without authentication. "
            "Assuming non-free agent."
        )
        return False

    try:
        # Build headers - try both token and x-api-key for compatibility
        # Payment endpoints use "token", registry might use "x-api-key"
        headers = {
            "Content-Type": "application/json",
            "token": payment_api_key,
            "x-api-key": payment_api_key
        }
        logging.info(f"Registry auth: Using API key {payment_api_key[:8] if payment_api_key else 'NONE'}... (masked)")

        # Registry endpoint is under /api/v1/ on the payment service
        # Use the payment_service_url directly (it already includes /api/v1)
        base_url = payment_service_url.rstrip('/')

        # Query registry endpoint: /registry/agent-identifier with query params
        # NOT /registry/{id} - the path is literally "agent-identifier"
        url = f"{base_url}/registry/agent-identifier"
        params = {
            "agentIdentifier": agent_identifier,
            "network": network
        }
        logging.info(f"Querying registry at: {url}?agentIdentifier={agent_identifier[:8]}...&network={network}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_text = await response.text()

                if response.status == 404:
                    # Agent not found in registry - assume not free
                    logging.warning(
                        f"Agent {agent_identifier[:8]}... not found in registry (404). "
                        f"Response: {response_text}. "
                        "Assuming non-free agent. Register your agent first."
                    )
                    return False

                if response.status != 200:
                    logging.error(
                        f"Registry query failed with status {response.status}. "
                        f"Response: {response_text}. "
                        "Assuming non-free agent."
                    )
                    return False

                # Parse response
                try:
                    data = await response.json()
                except Exception as e:
                    logging.error(f"Failed to parse registry response as JSON: {response_text}. Error: {e}")
                    return False

                logging.info(f"Registry response for agent {agent_identifier[:8]}...: {data}")

                # Check if agent is marked as free
                agent_data = data.get("data", {})
                metadata = agent_data.get("Metadata", {})
                agent_pricing = metadata.get("AgentPricing", {})

                # Check 1: pricingType field (most common for free agents)
                pricing_type = agent_pricing.get("pricingType", "")
                is_free = pricing_type.lower() == "free"

                # Check 2: If pricingType is not "Free", check Pricing array for amount "0"
                if not is_free:
                    pricing_list = agent_pricing.get("Pricing", [])
                    if pricing_list:
                        is_free = all(
                            str(price.get("amount", "1")) == "0"
                            for price in pricing_list
                        )

                # Check 3: Explicit isFree field as fallback
                if not is_free:
                    is_free = agent_data.get("isFree", False) or agent_data.get("is_free", False)

                logging.info(
                    f"Agent {agent_identifier[:8]}... registry check: "
                    f"{'FREE agent' if is_free else 'PAID agent'}"
                )

                return is_free

    except aiohttp.ClientError as e:
        logging.error(
            f"Network error querying registry for agent {agent_identifier[:8]}...: {e}. "
            "Assuming non-free agent."
        )
        return False
    except Exception as e:
        logging.error(
            f"Unexpected error querying registry for agent {agent_identifier[:8]}...: {e}. "
            "Assuming non-free agent."
        )
        return False
