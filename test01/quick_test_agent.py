#!/usr/bin/env python3
from masumi import run

async def process_job(identifier_from_purchaser: str, input_data: dict):
    """Simple test agent - uppercase text"""
    text = input_data.get("text", "")
    return {
        "result": text.upper(),
        "from": identifier_from_purchaser,
        "message": "✅ Latest Masumi changes working!"
    }

INPUT_SCHEMA = {
    "input_data": [
        {"id": "text", "type": "string", "name": "Text to Process"}
    ]
}

if __name__ == "__main__":
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
    )
