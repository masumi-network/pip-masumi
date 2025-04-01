import hashlib
import canonicaljson
import logging as logger

def _hash_input(input_data: dict, identifier_from_purchaser: str) -> str:
        """Hash the input data using SHA-256 with canonical JSON encoding."""

        # Convert the input data to a canonical JSON string using canonicaljson
        input_json = canonicaljson.encode_canonical_json(input_data).decode('utf-8')
        logger.debug(f"Canonical Input JSON: {input_json}")

        # Add the identifier_from_purchaser to the input JSON
        input_json = identifier_from_purchaser + input_json
        logger.debug(f"Input JSON with purchaser identifier: {input_json}")

        # Hash the input JSON string using SHA-256
        return hashlib.sha256(input_json.encode()).hexdigest()
