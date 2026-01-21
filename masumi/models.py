"""
Pydantic models for MIP-003 request and response structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StartJobRequest(BaseModel):
    """Request model for /start_job endpoint"""
    identifier_from_purchaser: str = Field(..., description="Purchaser-defined identifier")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data matching the input schema")
    
    class Config:
        json_schema_extra = {
            "example": {
                "identifier_from_purchaser": "resume-job-123",
                "input_data": {
                    "text": "Write a story about a robot learning to paint"
                }
            }
        }


class StartJobResponse(BaseModel):
    """Response model for /start_job endpoint"""
    id: str = Field(..., description="Unique identifier for the started job")
    blockchainIdentifier: str = Field(..., description="Unique identifier for payment")
    payByTime: int = Field(..., description="Unix timestamp for payment deadline")
    submitResultTime: int = Field(..., description="Unix timestamp until which result must be submitted")
    unlockTime: int = Field(..., description="Unix timestamp when payment can be unlocked")
    externalDisputeUnlockTime: int = Field(..., description="Unix timestamp until when disputes can happen")
    agentIdentifier: str = Field(..., description="Agent Identifier")
    sellerVKey: str = Field(..., description="Wallet Public Key")
    identifierFromPurchaser: str = Field(..., description="Echoes back the identifier from purchaser")
    input_hash: str = Field(..., alias="input_hash", description="Hash of the input data")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "18d66eed-6af5-4589-b53a-d2e78af657b6",
                "blockchainIdentifier": "block_789def",
                "payByTime": 1721480200,
                "submitResultTime": 1717171717,
                "unlockTime": 1717172717,
                "externalDisputeUnlockTime": 1717173717,
                "agentIdentifier": "resume-wizard-v1",
                "sellerVKey": "addr1qxlkjl23k4jlksdjfl234jlksdf",
                "identifierFromPurchaser": "resume-job-123",
                "input_hash": "a87ff679a2f3e71d9181a67b7542122c"
            }
        }


class StatusResponse(BaseModel):
    """Response model for /status endpoint"""
    id: str = Field(..., description="Unique identifier of the status")
    status: str = Field(..., description="Current status of the job")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Only required when status is 'awaiting_input'")
    result: Optional[str] = Field(None, description="Job result or pre-result, if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "8731ecb3-3bcc-4ebc-b46ff7dd12dd",
                "status": "completed",
                "result": "Resume generated successfully"
            }
        }


class ProvideInputRequest(BaseModel):
    """Request model for /provide_input endpoint"""
    job_id: str = Field(..., description="The ID of the job")
    status_id: Optional[str] = Field(None, description="Status ID if needed")
    input_data: Dict[str, Any] = Field(..., description="Additional input data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "18d66eed-6af5-4589-b53a-d2e78af657b6",
                "status_id": "status-123",
                "input_data": {
                    "additional_info": "More information"
                }
            }
        }


class AvailabilityResponse(BaseModel):
    """Response model for /availability endpoint"""
    status: str = Field(..., description="Server status (available or unavailable)")
    type: str = Field(default="masumi-agent", description="Service type identifier")
    message: Optional[str] = Field(None, description="Additional message or details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "available",
                "type": "masumi-agent",
                "message": "Resume Generator is ready to accept jobs"
            }
        }


class ValidationRule(BaseModel):
    """Validation rule structure"""
    validation: str = Field(..., description="Type of validation (min, max, format, accept, optional)")
    value: str = Field(..., description="Validation value")


class InputField(BaseModel):
    """Input field structure for input schema according to MIP-003 Attachment 01"""
    id: str = Field(..., description="Unique identifier of the input field")
    type: str = Field(..., description="Type of input (text, textarea, number, boolean, option, none, email, password, tel, url, date, datetime-local, time, month, week, color, range, file, hidden, search, checkbox, radio)")
    name: str = Field(..., description="Displayed name for the input field")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data specific to the input type (placeholder, description, default, values, etc.)")
    validations: Optional[List[ValidationRule]] = Field(None, description="Array of validation rules")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "full_name",
                "type": "text",
                "name": "Full Name",
                "data": {
                    "placeholder": "Enter your full name",
                    "description": "Your first and last name"
                },
                "validations": [
                    {"validation": "min", "value": "3"},
                    {"validation": "max", "value": "100"}
                ]
            }
        }


class InputGroup(BaseModel):
    """Input group structure for grouped inputs"""
    id: str = Field(..., description="Unique identifier of the group")
    title: str = Field(..., description="Title of the group")
    input_data: List[InputField] = Field(..., description="Array of input field definitions")


class InputSchemaResponse(BaseModel):
    """Response model for /input_schema endpoint"""
    input_data: Optional[List[InputField]] = Field(None, description="Array of input field definitions")
    input_groups: Optional[List[InputGroup]] = Field(None, description="Grouped input definitions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_data": [
                    {
                        "id": "text",
                        "type": "string",
                        "name": "Text to process"
                    }
                ]
            }
        }


class DemoResponse(BaseModel):
    """Response model for /demo endpoint"""
    input: Dict[str, Any] = Field(..., description="Example input data")
    output: Dict[str, str] = Field(..., description="Example output containing the result")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": {
                    "text": "Write a story about a robot"
                },
                "output": {
                    "result": "Once upon a time, a robot learned to paint..."
                }
            }
        }


