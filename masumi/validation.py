"""
Input schema validation according to MIP-003 Attachment 01.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .models import InputField, ValidationRule
from .helper_functions import setup_logging

logger = setup_logging(__name__)


class ValidationError(Exception):
    """
    Raised when input validation fails.
    
    Contains validation error information useful for debugging and admin interface.
    """
    def __init__(self, message: str, field_errors: Optional[Dict[str, List[str]]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field_errors: Optional dict mapping field IDs to list of error messages for that field
        """
        super().__init__(message)
        self.message = message
        self.field_errors = field_errors or {}


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


def validate_date_format(value: str) -> bool:
    """Validate date format (YYYY-MM-DD) with valid month (01-12) and day ranges."""
    if not isinstance(value, str):
        return False
    # HTML date input format: YYYY-MM-DD - use datetime for semantic validation (rejects 2025-13-32, etc.)
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_datetime_local_format(value: str) -> bool:
    """Validate datetime-local format (YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.sss) with valid ranges.
    Per HTML spec, datetime-local must have NO timezone information (strptime rejects +05:00, Z, etc.)."""
    if not isinstance(value, str):
        return False
    # Use strptime (not fromisoformat) to reject timezone offsets - HTML datetime-local is local-only
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def validate_time_format(value: str) -> bool:
    """Validate time format (HH:MM or HH:MM:SS or HH:MM:SS.sss) with valid ranges (hours 00-23, minutes/seconds 00-59)."""
    if not isinstance(value, str):
        return False
    # Use datetime parsing for semantic validation (rejects 25:00, 12:60, etc.)
    # All branches use strptime so variable-width components (e.g. "9:5" or "9:5:3.123") are accepted consistently.
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        pass
    try:
        datetime.strptime(value, "%H:%M:%S")
        return True
    except ValueError:
        pass
    try:
        datetime.strptime(value, "%H:%M:%S.%f")
        return True
    except ValueError:
        pass
    return False


def validate_month_format(value: str) -> bool:
    """Validate month format (YYYY-MM) with valid month range (01-12)."""
    if not isinstance(value, str):
        return False
    # HTML month input format: YYYY-MM - use strptime for consistency with validate_date_format
    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except ValueError:
        return False


def validate_week_format(value: str) -> bool:
    """Validate week format (YYYY-Www) with ISO 8601 week number range (01-53)."""
    if not isinstance(value, str):
        return False
    # HTML week input format: YYYY-Www (e.g., 2025-W01)
    # ISO 8601 specifies week numbers must be in range 01-53
    # Note: W53 is accepted for all years. Full ISO 8601 enforcement (W53 only exists in
    # certain years) would require isocalendar() checks and is not enforced by browsers either.
    pattern = r'^\d{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$'
    return bool(re.match(pattern, value))


def validate_format(value: Any, format_type: str) -> bool:
    """Validate value format based on format type."""
    format_validators = {
        "email": validate_email,
        "url": validate_url,
        "nonempty": validate_nonempty,
        "integer": validate_integer,
        "tel-pattern": validate_tel_pattern,
        "date": validate_date_format,
        "datetime-local": validate_datetime_local_format,
        "time": validate_time_format,
        "month": validate_month_format,
        "week": validate_week_format,
    }
    
    validator = format_validators.get(format_type)
    if not validator:
        logger.warning(f"Unknown format type: {format_type}")
        return True  # Don't fail validation for unknown formats
    
    return validator(value)


def validate_min(value: Any, min_value: str, field_type: str) -> bool:
    """Validate minimum value/length."""
    # Handle date/time types with string comparison
    date_time_types = ("date", "datetime-local", "time", "month", "week")
    if field_type in date_time_types:
        if not isinstance(value, str):
            return False
        try:
            # Simple string comparison for date/time values
            return value >= min_value
        except (ValueError, TypeError):
            return False
    
    try:
        min_val = int(min_value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid min value: {min_value}")
        return True
    
    # Handle text-like types for length validation
    text_types = ("text", "textarea", "email", "password", "tel", "url", "search", "hidden")
    if field_type in text_types:
        return len(str(value)) >= min_val
    elif field_type == "number" or field_type == "range":
        try:
            num_val = float(value)
            return num_val >= min_val
        except (ValueError, TypeError):
            return False
    elif field_type in ("option", "checkbox", "radio"):
        # For option/checkbox/radio types, count selected values
        if isinstance(value, list):
            num_val = len(value)
        else:
            num_val = 1 if value else 0
        return num_val >= min_val
    return True


def validate_max(value: Any, max_value: str, field_type: str) -> bool:
    """Validate maximum value/length."""
    # Handle date/time types with string comparison
    date_time_types = ("date", "datetime-local", "time", "month", "week")
    if field_type in date_time_types:
        if not isinstance(value, str):
            return False
        try:
            # Simple string comparison for date/time values
            return value <= max_value
        except (ValueError, TypeError):
            return False
    
    try:
        max_val = int(max_value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid max value: {max_value}")
        return True
    
    # Handle text-like types for length validation
    text_types = ("text", "textarea", "email", "password", "tel", "url", "search", "hidden")
    if field_type in text_types:
        return len(str(value)) <= max_val
    elif field_type == "number" or field_type == "range":
        try:
            num_val = float(value)
            return num_val <= max_val
        except (ValueError, TypeError):
            return False
    elif field_type in ("option", "checkbox", "radio"):
        # For option/checkbox/radio types, count selected values
        if isinstance(value, list):
            num_val = len(value)
        else:
            num_val = 1 if value else 0
        return num_val <= max_val
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


def is_field_optional(field: InputField) -> bool:
    """Check if field is optional based on validations."""
    if not field.validations:
        return False
    
    for validation in field.validations:
        # Handle both ValidationRule objects and dicts
        if isinstance(validation, dict):
            if validation.get("validation") == "optional":
                return True
        else:
            if validation.validation == "optional":
                return True
    return False


def normalize_field_type(field_type: str) -> str:
    """Normalize field type for backward compatibility."""
    # Map old type names to new ones
    type_mapping = {
        "string": "text",
    }
    return type_mapping.get(field_type, field_type)


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
    field_type = normalize_field_type(field.type)
    
    # Check if field is optional
    is_optional = is_field_optional(field)
    
    # According to MIP-003: fields are required by default unless optional validation is set
    if not is_optional and not validate_required(value):
        errors.append(f"Field '{field_id}' is required")
        return errors  # Don't check other validations if required is missing
    
    # If optional and value is empty/None, skip other validations
    if is_optional and (value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and len(value) == 0)):
        return errors
    
    # Type validation
    # Handle text-like types (text, textarea, email, password, tel, url, search, hidden)
    text_types = ("text", "textarea", "email", "password", "tel", "url", "search", "hidden")
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
        # Option can be a string (single select) or list (multi-select)
        if not isinstance(value, (str, list)):
            errors.append(f"Field '{field_id}' must be a string or list")
    elif field_type == "radio":
        # Radio should be a string (single selection)
        if not isinstance(value, str):
            errors.append(f"Field '{field_id}' must be a string")
    elif field_type in ("date", "datetime-local", "time", "month", "week"):
        if not isinstance(value, str):
            errors.append(f"Field '{field_id}' must be a string")
    elif field_type == "range":
        try:
            float(value)
        except (ValueError, TypeError):
            errors.append(f"Field '{field_id}' must be a number")
    elif field_type == "color":
        if not isinstance(value, str):
            errors.append(f"Field '{field_id}' must be a string")
    elif field_type == "file":
        if not isinstance(value, str):
            errors.append(f"Field '{field_id}' must be a string (URL)")
    elif field_type == "none":
        # Display-only field, no validation needed
        pass
    
    # Auto-validate format for email, url, and date/time types (per MIP-003 spec)
    # Direct call here (not via validate_format) because type-based validation
    # is separate from explicit format validation rules in the validations array.
    if field_type == "email" and isinstance(value, str):
        if not validate_email(value):
            errors.append(f"Field '{field_id}' must be a valid email address")
    elif field_type == "url" and isinstance(value, str):
        if not validate_url(value):
            errors.append(f"Field '{field_id}' must be a valid URL")
    elif field_type == "date" and isinstance(value, str):
        if not validate_date_format(value):
            errors.append(f"Field '{field_id}' must be a valid date in YYYY-MM-DD format")
    elif field_type == "datetime-local" and isinstance(value, str):
        if not validate_datetime_local_format(value):
            errors.append(f"Field '{field_id}' must be a valid datetime in YYYY-MM-DDTHH:MM[:SS[.sss]] format")
    elif field_type == "time" and isinstance(value, str):
        if not validate_time_format(value):
            errors.append(f"Field '{field_id}' must be a valid time in HH:MM[:SS[.sss]] format")
    elif field_type == "month" and isinstance(value, str):
        if not validate_month_format(value):
            errors.append(f"Field '{field_id}' must be a valid month in YYYY-MM format")
    elif field_type == "week" and isinstance(value, str):
        if not validate_week_format(value):
            errors.append(f"Field '{field_id}' must be a valid week in YYYY-Www format")
    
    # Process validations array
    if field.validations:
        for validation_rule in field.validations:
            # Handle both ValidationRule objects and dicts
            if isinstance(validation_rule, dict):
                validation_type = validation_rule.get("validation")
                validation_value = validation_rule.get("value")
            else:
                validation_type = validation_rule.validation
                validation_value = validation_rule.value
            
            if not validation_type or not validation_value:
                continue
            
            if validation_type == "min":
                if not validate_min(value, validation_value, field_type):
                    errors.append(f"Field '{field_id}' must be at least {validation_value}")
            elif validation_type == "max":
                if not validate_max(value, validation_value, field_type):
                    errors.append(f"Field '{field_id}' must be at most {validation_value}")
            elif validation_type == "format":
                if not validate_format(value, validation_value):
                    errors.append(f"Field '{field_id}' must match format: {validation_value}")
            elif validation_type == "accept":
                if not validate_accept(value, validation_value, field_type):
                    errors.append(f"Field '{field_id}' file type not accepted")
            # "optional" validation is already handled above
    
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
            # Handle backward compatibility: if name is missing, use id as name
            if "name" not in field_dict:
                field_dict["name"] = field_dict.get("id", "Unnamed Field")
            
            # Convert validations from dicts to ValidationRule objects if needed
            if "validations" in field_dict and field_dict["validations"]:
                validation_list = []
                for val in field_dict["validations"]:
                    if isinstance(val, dict):
                        validation_list.append(ValidationRule(**val))
                    else:
                        validation_list.append(val)
                field_dict["validations"] = validation_list
            
            field_objects.append(InputField(**field_dict))
        else:
            field_objects.append(field_dict)
    
    # Build a map of field IDs to field definitions
    field_map = {field.id: field for field in field_objects}
    
    # Collect errors by field for structured error reporting
    field_errors_dict: Dict[str, List[str]] = {}
    
    # Validate each field in input_data
    for field_id, value in input_data.items():
        if field_id not in field_map:
            # Field not in schema - might be okay, but log a warning
            logger.warning(f"Field '{field_id}' not defined in schema")
            continue
        
        field = field_map[field_id]
        field_errors = validate_field_value(value, field)
        if field_errors:
            field_errors_dict[field_id] = field_errors
            errors.extend(field_errors)
    
    # Check for required fields that are missing
    # According to MIP-003: fields are required by default unless optional validation is set
    for field in field_objects:
        if field.id not in input_data:
            if not is_field_optional(field):
                error_msg = f"Required field '{field.id}' is missing"
                errors.append(error_msg)
                if field.id not in field_errors_dict:
                    field_errors_dict[field.id] = []
                field_errors_dict[field.id].append(error_msg)
    
    if errors:
        error_message = "Validation failed: " + "; ".join(errors)
        logger.error(error_message)
        # Include structured field errors for admin interface
        raise ValidationError(error_message, field_errors=field_errors_dict)
    
    logger.debug("Input data validation passed")
