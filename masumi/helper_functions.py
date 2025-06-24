import hashlib
import canonicaljson
import logging as logger

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
    This function uses the raw output string as the payload.
    """
    # Step 2.1: The output is a raw string, so no special processing is needed.
    # Call the core hashing function with the raw data.
    return _create_hash_from_payload(output_string, identifier_from_purchaser)

# Legacy function names for backward compatibility
def _hash_input(input_data: dict, identifier_from_purchaser: str) -> str:
    """Legacy function - use create_masumi_input_hash instead."""
    return create_masumi_input_hash(input_data, identifier_from_purchaser)

def _hash_output(output_data: dict) -> str:
    """Legacy function - NOTE: This function signature is deprecated and doesn't follow MIP-004."""
    # For backward compatibility, convert dict to JSON string and hash without identifier
    output_json = canonicaljson.encode_canonical_json(output_data).decode('utf-8')
    logger.debug(f"Canonical Output JSON: {output_json}")
    return hashlib.sha256(output_json.encode()).hexdigest()

