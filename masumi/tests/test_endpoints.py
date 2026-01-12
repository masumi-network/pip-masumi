"""
Tests for endpoint handlers, validation, and FastAPI integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from masumi.endpoints import AgentEndpointHandler
from masumi.validation import validate_input_data, ValidationError
from masumi.job_manager import JobManager, InMemoryJobStorage
from masumi.config import Config


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    return Config(
        payment_service_url="https://test.payment.masumi.network/api/v1",
        payment_api_key="test_api_key"
    )


@pytest.fixture
def endpoint_handler():
    """Create an endpoint handler for testing."""
    return AgentEndpointHandler()


@pytest.mark.asyncio
async def test_start_job_handler_registration(endpoint_handler):
    """Test registering a start_job handler."""
    
    @endpoint_handler.start_job
    async def test_handler(identifier: str, input_data: dict):
        return "result"
    
    handler = endpoint_handler.get_start_job_handler()
    assert handler is not None
    assert handler == test_handler


def test_input_schema_static(endpoint_handler):
    """Test registering a static input_schema (dict) - RECOMMENDED."""
    schema_dict = {"input_data": [{"id": "test", "type": "string"}]}
    
    # Test using decorator
    result = endpoint_handler.input_schema(schema_dict)
    assert result == schema_dict
    
    # Test getting it back
    retrieved_schema = endpoint_handler.get_input_schema()
    assert retrieved_schema == schema_dict


def test_input_schema_dynamic(endpoint_handler):
    """Test registering a dynamic input_schema (callable) - OPTIONAL."""
    schema_dict = {"input_data": [{"id": "test", "type": "string"}]}
    
    def get_schema():
        return schema_dict
    
    # Test using decorator
    result = endpoint_handler.input_schema(get_schema)
    assert result == get_schema
    
    # Test getting it back (should call the function)
    retrieved_schema = endpoint_handler.get_input_schema()
    assert retrieved_schema == schema_dict


def test_input_schema_set_directly(endpoint_handler):
    """Test setting input_schema directly (both static and dynamic)."""
    # Test static
    schema_dict = {"input_data": [{"id": "test", "type": "string"}]}
    endpoint_handler.set_input_schema_handler(schema_dict)
    retrieved_schema = endpoint_handler.get_input_schema()
    assert retrieved_schema == schema_dict
    
    # Test dynamic
    def get_schema():
        return {"input_data": [{"id": "dynamic", "type": "string"}]}
    endpoint_handler.set_input_schema_handler(get_schema)
    retrieved_schema = endpoint_handler.get_input_schema()
    assert retrieved_schema["input_data"][0]["id"] == "dynamic"


def test_validation_string_field():
    """Test validating a string field."""
    schema = {
        "input_data": [
            {
                "id": "text",
                "type": "string",
                "name": "Text"
            }
        ]
    }
    
    # Valid input
    validate_input_data({"text": "hello"}, schema)
    
    # Missing optional field - should not raise
    validate_input_data({}, schema)


def test_validation_required_field():
    """Test validating required fields."""
    schema = {
        "input_data": [
            {
                "id": "text",
                "type": "string",
                "name": "Text",
                "validations": [
                    {"validation": "required", "value": "true"}
                ]
            }
        ]
    }
    
    # Valid - field provided
    validate_input_data({"text": "hello"}, schema)
    
    # Invalid - required field missing
    with pytest.raises(ValidationError):
        validate_input_data({}, schema)


def test_validation_email_format():
    """Test validating email format."""
    schema = {
        "input_data": [
            {
                "id": "email",
                "type": "string",
                "name": "Email",
                "validations": [
                    {"validation": "format", "value": "email"}
                ]
            }
        ]
    }
    
    # Valid email
    validate_input_data({"email": "test@example.com"}, schema)
    
    # Invalid email
    with pytest.raises(ValidationError):
        validate_input_data({"email": "not-an-email"}, schema)


def test_validation_min_max_length():
    """Test validating min/max length for strings."""
    schema = {
        "input_data": [
            {
                "id": "text",
                "type": "string",
                "name": "Text",
                "validations": [
                    {"validation": "min", "value": "3"},
                    {"validation": "max", "value": "10"}
                ]
            }
        ]
    }
    
    # Valid length
    validate_input_data({"text": "hello"}, schema)
    
    # Too short
    with pytest.raises(ValidationError):
        validate_input_data({"text": "hi"}, schema)
    
    # Too long
    with pytest.raises(ValidationError):
        validate_input_data({"text": "this is too long"}, schema)


def test_validation_option_field():
    """Test validating option fields."""
    schema = {
        "input_data": [
            {
                "id": "choice",
                "type": "option",
                "name": "Choice",
                "data": {
                    "values": ["option1", "option2", "option3"]
                }
            }
        ]
    }
    
    # Valid option
    validate_input_data({"choice": "option1"}, schema)
    
    # Invalid option
    with pytest.raises(ValidationError):
        validate_input_data({"choice": "invalid_option"}, schema)


def test_in_memory_job_storage():
    """Test InMemoryJobStorage."""
    storage = InMemoryJobStorage()
    
    # Test create and get
    job_data = {"job_id": "test-123", "status": "pending"}
    asyncio.run(storage.create_job("test-123", job_data))
    
    retrieved = asyncio.run(storage.get_job("test-123"))
    assert retrieved is not None
    assert retrieved["status"] == "pending"
    
    # Test update
    asyncio.run(storage.update_job("test-123", {"status": "completed"}))
    updated = asyncio.run(storage.get_job("test-123"))
    assert updated["status"] == "completed"
    
    # Test list
    jobs = asyncio.run(storage.list_jobs())
    assert len(jobs) == 1
    
    # Test delete
    asyncio.run(storage.delete_job("test-123"))
    deleted = asyncio.run(storage.get_job("test-123"))
    assert deleted is None


def test_job_manager():
    """Test JobManager."""
    manager = JobManager()
    
    # Create a job
    payment_mock = AsyncMock()
    job_id = asyncio.run(manager.create_job(
        identifier_from_purchaser="purchaser-123",
        input_data={"text": "test"},
        payment=payment_mock,  # AsyncMock payment instance
        blockchain_identifier="blockchain-123",
        pay_by_time=1234567890,
        submit_result_time=1234567900,
        unlock_time=1234568000,
        external_dispute_unlock_time=1234569000,
        agent_identifier="agent-123",
        seller_vkey="seller-key-123"
    ))
    
    assert job_id is not None
    
    # Get job
    job = asyncio.run(manager.get_job(job_id))
    assert job is not None
    assert job["status"] == "awaiting_payment"
    
    # Update status
    asyncio.run(manager.set_job_running(job_id))
    job = asyncio.run(manager.get_job(job_id))
    assert job["status"] == "running"
    
    # Complete job
    asyncio.run(manager.set_job_completed(job_id, "result"))
    job = asyncio.run(manager.get_job(job_id))
    assert job["status"] == "completed"
    assert job["result"] == "result"


@pytest.mark.asyncio
async def test_endpoint_handler_all_handlers(endpoint_handler):
    """Test registering all handler types."""
    
    @endpoint_handler.start_job
    async def start_job(identifier: str, input_data: dict):
        return "result"
    
    @endpoint_handler.status
    async def status(job_id: str):
        return {"status": "completed"}
    
    @endpoint_handler.availability
    async def availability():
        return {"status": "available"}
    
    # Use static schema for this test
    endpoint_handler.input_schema({"input_data": []})
    
    @endpoint_handler.provide_input
    async def provide_input(job_id: str, input_data: dict):
        return "ok"
    
    @endpoint_handler.demo
    def demo():
        return {"input": {}, "output": {"result": "demo"}}
    
    # Verify all handlers are set
    assert endpoint_handler.get_start_job_handler() is not None
    assert endpoint_handler.get_status_handler() is not None
    assert endpoint_handler.get_availability_handler() is not None
    assert endpoint_handler.get_input_schema() is not None
    assert endpoint_handler.get_provide_input_handler() is not None
    assert endpoint_handler.get_demo_handler() is not None
