import hashlib
import json
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
    This function uses the raw output string as the payload and applies
    JSON escaping to match the reference implementation.
    """
    if not isinstance(output_string, str):
        raise TypeError("output_string must be a string")

    # Step 2.1: Escape special characters in the result string using JSON encoding
    escaped_output = json.dumps(output_string, ensure_ascii=False)[1:-1]

    # Call the core hashing function with the processed data.
    return _create_hash_from_payload(escaped_output, identifier_from_purchaser)
