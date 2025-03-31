import hashlib
import json
import logging as logger

def _hash_input(input_data: dict, identifier_from_purchaser: str) -> str:
        """Hash the input data using SHA-256."""

        # Convert the input data to a JSON string
        input_json = json.dumps(input_data)
        logger.debug(f"Input JSON: {input_json}")

        # Add the identifier_from_purchaser to the input JSON
        input_json = identifier_from_purchaser + input_json
        logger.debug(f"Input JSON with purchaser identifier: {input_json}")

        # Hash the input JSON string using SHA-256
        return hashlib.sha256(input_json.encode()).hexdigest()
