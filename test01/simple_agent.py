#!/usr/bin/env python3
from masumi import run

async def process_job(identifier_from_purchaser: str, input_data: dict):
    text = input_data.get("text", "")
    return {
        "result": f"PROCESSED: {text.upper()}",
        "from": identifier_from_purchaser
    }

INPUT_SCHEMA = {
    "input_data": [
        {"id": "text", "type": "string", "name": "Text Input"}
    ]
}

if __name__ == "__main__":
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
    )
