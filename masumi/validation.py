"""
Input schema validation according to MIP-003 Attachment 01.
"""

import re
import logging
from typing import Dict, Any, List
from .models import InputField

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_email(value: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))


def validate_url(value: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?$'
    return bool(re.match(pattern, value))


def validate_nonempty(value: Any) -> bool:
    """Validate that value is not empty."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True


def validate_integer(value: Any) -> bool:
    """Validate that value is an integer."""
    try:
        if isinstance(value, (int, float)):
            return float(value).is_integer()
        if isinstance(value, str):
            float_val = float(value)
            return float_val.is_integer()
        return False
    except (ValueError, TypeError):
        return False


def validate_tel_pattern(value: str) -> bool:
    """Validate telephone number pattern (basic validation)."""
    if not isinstance(value, str):
        return False
    # Basic tel pattern: allows digits, spaces, dashes, parentheses, plus sign
    pattern = r'^[\d\s\-\(\)\+]+$'
    return bool(re.match(pattern, value))


def validate_format(value: Any, format_type: str) -> bool:
    """Validate value format based on format type."""
    format_validators = {
        "email": validate_email,
        "url": validate_url,
        "nonempty": validate_nonempty,
        "integer": validate_integer,
        "tel-pattern": validate_tel_pattern,
    }
    
    validator = format_validators.get(format_type)
    if not validator:
        logger.warning(f"Unknown format type: {format_type}")
        return True  # Don't fail validation for unknown formats
    
    return validator(value)


def validate_min(value: Any, min_value: str, field_type: str) -> bool:
    """Validate minimum value/length."""
    try:
        min_val = int(min_value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid min value: {min_value}")
        return True
    
    # Handle text-like types for length validation
    text_types = ("text", "textarea", "email", "password", "tel", "url", "search", "hidden", "string")
    if field_type in text_types:
        return len(str(value)) >= min_val
    elif field_type in ("number", "option", "range", "date", "datetime-local", "time", "month", "week", "checkbox", "radio"):
        try:
            if field_type == "number":
                num_val = float(value)
            else:
                # For option type, count selected values
                if isinstance(value, list):
                    num_val = len(value)
                else:
                    num_val = 1 if value else 0
            return num_val >= min_val
        except (ValueError, TypeError):
            return False
    return True


def validate_max(value: Any, max_value: str, field_type: str) -> bool:
    """Validate maximum value/length."""
    try:
        max_val = int(max_value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid max value: {max_value}")
        return True
    
    # Handle text-like types for length validation
    text_types = ("text", "textarea", "email", "password", "tel", "url", "search", "hidden", "string")
    if field_type in text_types:
        return len(str(value)) <= max_val
    elif field_type in ("number", "option", "range", "date", "datetime-local", "time", "month", "week", "checkbox", "radio"):
        try:
            if field_type == "number":
                num_val = float(value)
            else:
                # For option type, count selected values
                if isinstance(value, list):
                    num_val = len(value)
                else:
                    num_val = 1 if value else 0
            return num_val <= max_val
        except (ValueError, TypeError):
            return False
    return True


def validate_required(value: Any) -> bool:
    """Validate that a required field is present."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True


def validate_accept(value: Any, accept_value: str, field_type: str) -> bool:
    """
    Validate file type against accept pattern.
    
    Args:
        value: The file value (URL string for file type)
        accept_value: Comma-separated list of accepted file types (e.g., "image/*,.pdf,.doc")
        field_type: The field type (should be "file")
    
    Returns:
        bool: True if file type is accepted (or if not a file type)
    """
    if field_type != "file":
        return True  # Only applies to file type
    
    if not isinstance(value, str):
        return False
    
    # For file type with outputFormat: url, the value is a URL string
    # We can't validate the actual file type from URL without fetching it
    # So we'll do basic validation - if it's a URL, accept it
    # In a real implementation, you might want to fetch and check the file
    if value.startswith(("http://", "https://")):
        return True
    
    # If not a URL, might be a filename - check extension
    # Parse accept patterns (e.g., "image/*,.pdf,.doc")
    accept_patterns = [p.strip() for p in accept_value.split(",")]
    
    # Extract file extension from value
    if "." in value:
        ext = value.split(".")[-1].lower()
        for pattern in accept_patterns:
            if pattern == "*" or pattern == f"*.{ext}" or pattern == f".{ext}":
                return True
            if pattern.endswith("/*") and ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                return True
    
    return False


def validate_field_value(value: Any, field: InputField) -> List[str]:
    """
    Validate a single field value against its schema definition.
    
    Args:
        value: The value to validate
        field: The field definition from the input schema
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    field_id = field.id
    field_type = field.type
    
    # According to MIP-003: fields are required by default
    # Use "optional" validation to make a field optional
    is_optional = False
    if field.validations:
        for validation in field.validations:
            if validation.validation == "optional":
                # Check if optional value is "true" or truthy
                opt_value = validation.value
                if isinstance(opt_value, str):
                    is_optional = opt_value.lower() in ("true", "1", "yes")
                else:
                    is_optional = bool(opt_value)
                break
    
    # Check required (if not optional)
    if not is_optional and not validate_required(value):
        errors.append(f"Field '{field_id}' is required")
        return errors  # Don't check other validations if required is missing
    
    # If value is None/empty and optional, skip other validations
    if is_optional and (value is None or (isinstance(value, str) and not value.strip())):
        return errors
    
    # Type validation
    # Handle text-like types (text, textarea, email, password, tel, url, search, hidden)
    text_types = ("text", "textarea", "email", "password", "tel", "url", "search", "hidden", "string")
    if field_type in text_types and not isinstance(value, str):
        errors.append(f"Field '{field_id}' must be a string")
    elif field_type == "number":
        try:
            float(value)
        except (ValueError, TypeError):
            errors.append(f"Field '{field_id}' must be a number")
    elif field_type in ("boolean", "checkbox") and not isinstance(value, bool):
        errors.append(f"Field '{field_id}' must be a boolean")
    elif field_type == "option":
        if field.data and field.data.values:
            if isinstance(value, list):
                invalid = [v for v in value if v not in field.data.values]
                if invalid:
                    errors.append(f"Field '{field_id}' contains invalid options: {invalid}")
            elif value not in field.data.values:
                errors.append(f"Field '{field_id}' must be one of: {', '.join(field.data.values)}")
    
    # Auto-validate format for email and url types (per MIP-003 spec)
    if field_type == "email" and isinstance(value, str):
        if not validate_email(value):
            errors.append(f"Field '{field_id}' must be a valid email address")
    elif field_type == "url" and isinstance(value, str):
        if not validate_url(value):
            errors.append(f"Field '{field_id}' must be a valid URL")
    
    # Apply validation rules
    if field.validations:
        for validation in field.validations:
            validation_type = validation.validation
            validation_value = validation.value
            
            if validation_type == "format":
                if not validate_format(value, validation_value):
                    errors.append(f"Field '{field_id}' has invalid format (expected {validation_value})")
            elif validation_type == "min":
                if not validate_min(value, validation_value, field_type):
                    errors.append(f"Field '{field_id}' is below minimum value of {validation_value}")
            elif validation_type == "max":
                if not validate_max(value, validation_value, field_type):
                    errors.append(f"Field '{field_id}' exceeds maximum value of {validation_value}")
            elif validation_type == "accept":
                if not validate_accept(value, validation_value, field_type):
                    errors.append(f"Field '{field_id}' file type not accepted (expected: {validation_value})")
            elif validation_type == "optional":
                # Already checked above
                pass
            else:
                logger.warning(f"Unknown validation type: {validation_type}")
    
    return errors


def validate_input_data(
    input_data: Dict[str, Any],
    schema: Dict[str, Any]
) -> None:
    """
    Validate input data against an input schema.
    
    Args:
        input_data: The input data to validate
        schema: The input schema definition (from /input_schema endpoint format)
                Can be a dict with 'input_data' or 'input_groups', or already be InputSchemaResponse-like
        
    Raises:
        ValidationError: If validation fails
    """
    """
    Validate input data against an input schema.
    
    Args:
        input_data: The input data to validate
        schema: The input schema definition (from /input_schema endpoint format)
        
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    
    # Handle input_groups format
    fields = []
    if "input_groups" in schema and schema["input_groups"]:
        for group in schema["input_groups"]:
            # Handle both dict and Pydantic model formats
            group_data = group if isinstance(group, dict) else group.dict() if hasattr(group, 'dict') else group.model_dump() if hasattr(group, 'model_dump') else group
            group_fields = group_data.get("input_data", [])
            fields.extend(group_fields)
    elif "input_data" in schema and schema["input_data"]:
        fields = schema["input_data"]
    else:
        # Empty schema - no validation needed
        logger.debug("Empty schema, skipping validation")
        return
    
    # Convert fields to dict format if they're Pydantic models
    fields_dict = []
    for field in fields:
        if isinstance(field, dict):
            fields_dict.append(field)
        elif hasattr(field, 'model_dump'):
            fields_dict.append(field.model_dump())
        elif hasattr(field, 'dict'):
            fields_dict.append(field.dict())
        else:
            fields_dict.append(field)
    
    # Build InputField objects from dicts
    field_objects = []
    for field_dict in fields_dict:
        if isinstance(field_dict, dict):
            field_objects.append(InputField(**field_dict))
        else:
            field_objects.append(field_dict)
    
    # Build a map of field IDs to field definitions
    field_map = {field.id: field for field in field_objects}
    
    # Validate each field in input_data
    for field_id, value in input_data.items():
        if field_id not in field_map:
            # Field not in schema - might be okay, but log a warning
            logger.warning(f"Field '{field_id}' not defined in schema")
            continue
        
        field = field_map[field_id]
        field_errors = validate_field_value(value, field)
        errors.extend(field_errors)
    
    # Check for required fields that are missing
    # According to MIP-003: fields are required by default unless marked as optional
    for field in field_objects:
        is_optional = False
        if field.validations:
            for validation in field.validations:
                if validation.validation == "optional":
                    # Check if optional value is "true" or truthy
                    opt_value = validation.value
                    if isinstance(opt_value, str):
                        is_optional = opt_value.lower() in ("true", "1", "yes")
                    else:
                        is_optional = bool(opt_value)
                    break
        
        # Field is required if not optional and missing from input_data
        if not is_optional and field.id not in input_data:
            errors.append(f"Required field '{field.id}' is missing")
    
    if errors:
        error_message = "Validation failed: " + "; ".join(errors)
        logger.error(error_message)
        raise ValidationError(error_message)
    
    logger.debug("Input data validation passed")
