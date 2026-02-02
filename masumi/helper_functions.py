import hashlib
import json
import canonicaljson
import logging as logger
import logging
import sys
import os


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


# Log level mapping from string to logging constant
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_log_level(level_str: str = None) -> int:
    """
    Get logging level from LOG_LEVEL environment variable or provided string.
    
    Args:
        level_str: Optional logging level string. If not provided, reads from LOG_LEVEL env var.
    
    Returns:
        int: Logging level constant (defaults to logging.INFO if invalid or not set)
    """
    if level_str is None:
        level_str = os.getenv("LOG_LEVEL", "INFO")
    
    level_str = level_str.upper()
    return LOG_LEVEL_MAP.get(level_str, logging.INFO)


def setup_logging(name, level=logging.INFO, use_colors=True, use_emojis=True):
    """
    Centralized logging configuration for Masumi modules.
    
    Configures a logger with a beautiful colored console handler if no handlers are present.
    This prevents duplicate handlers when the function is called multiple times.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (default: logging.INFO). Can be int or string (will be converted).
        use_colors: Whether to use colors (default: True, auto-detects TTY)
        use_emojis: Whether to use emojis for log levels (default: True)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = get_log_level(level)
    
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
