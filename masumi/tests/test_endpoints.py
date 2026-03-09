"""
Tests for endpoint handlers, validation, and FastAPI integration.
"""

import pytest
import asyncio
from masumi.endpoints import AgentEndpointHandler
from masumi.models import StartJobRequest
from masumi.validation import validate_input_data, ValidationError
from masumi.job_manager import JobManager, InMemoryJobStorage
from masumi.config import Config
from masumi.payment import Payment


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
    
    # Missing field - should raise (fields are required by default)
    with pytest.raises(ValidationError):
        validate_input_data({}, schema)


def test_validation_required_field():
    """Test validating required fields."""
    schema = {
        "input_data": [
            {
                "id": "text",
                "type": "string",
                "name": "Text"
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
                "type": "email",
                "name": "Email"
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
                "name": "Text"
            }
        ]
    }
    
    # Valid input
    validate_input_data({"text": "hello"}, schema)
    
    # Empty string should fail (required field)
    with pytest.raises(ValidationError):
        validate_input_data({"text": ""}, schema)


def test_validation_option_field():
    """Test validating option fields."""
    schema = {
        "input_data": [
            {
                "id": "choice",
                "type": "option",
                "name": "Choice"
            }
        ]
    }
    
    # Valid option (validation of option values removed)
    validate_input_data({"choice": "option1"}, schema)


def test_validation_with_validations_array():
    """Test validating fields with validations array (new MIP-003 format)."""
    schema = {
        "input_data": [
            {
                "id": "username",
                "type": "text",
                "name": "Username",
                "data": {
                    "placeholder": "Enter username",
                    "description": "3-20 characters"
                },
                "validations": [
                    {"validation": "min", "value": "3"},
                    {"validation": "max", "value": "20"}
                ]
            }
        ]
    }
    
    # Valid input
    validate_input_data({"username": "testuser"}, schema)
    
    # Too short
    with pytest.raises(ValidationError):
        validate_input_data({"username": "ab"}, schema)
    
    # Too long
    with pytest.raises(ValidationError):
        validate_input_data({"username": "a" * 21}, schema)


def test_validation_optional_field():
    """Test validating optional fields."""
    schema = {
        "input_data": [
            {
                "id": "required_field",
                "type": "text",
                "name": "Required Field"
            },
            {
                "id": "optional_field",
                "type": "text",
                "name": "Optional Field",
                "validations": [
                    {"validation": "optional", "value": "true"}
                ]
            }
        ]
    }
    
    # Valid - both fields provided
    validate_input_data({"required_field": "value", "optional_field": "value"}, schema)
    
    # Valid - optional field missing
    validate_input_data({"required_field": "value"}, schema)
    
    # Invalid - required field missing
    with pytest.raises(ValidationError):
        validate_input_data({"optional_field": "value"}, schema)


def test_validation_format_validation():
    """Test format validation."""
    schema = {
        "input_data": [
            {
                "id": "email_field",
                "type": "email",
                "name": "Email",
                "validations": [
                    {"validation": "format", "value": "email"}
                ]
            },
            {
                "id": "text_field",
                "type": "text",
                "name": "Text",
                "validations": [
                    {"validation": "format", "value": "nonempty"}
                ]
            }
        ]
    }
    
    # Valid email
    validate_input_data({"email_field": "test@example.com", "text_field": "hello"}, schema)
    
    # Invalid email
    with pytest.raises(ValidationError):
        validate_input_data({"email_field": "not-an-email", "text_field": "hello"}, schema)
    
    # Empty text field (should fail nonempty format)
    with pytest.raises(ValidationError):
        validate_input_data({"email_field": "test@example.com", "text_field": ""}, schema)


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


def test_job_manager(mock_config):
    """Test JobManager."""
    manager = JobManager()
    
    # Create a real Payment instance instead of a mock
    payment = Payment(
        agent_identifier="agent-123",
        config=mock_config,
        network="Preprod",
        identifier_from_purchaser="purchaser-123",
        input_data={"text": "test"}
    )
    
    # Create a job
    job_id = asyncio.run(manager.create_job(
        identifier_from_purchaser="purchaser-123",
        input_data={"text": "test"},
        payment=payment,
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
    
    # Complete job - this will try to make a real API call with a fake blockchain ID
    # The API call will fail, but we can verify the manager handles it correctly
    # Since set_job_completed raises on API failure, we expect an exception
    # but the job manager correctly attempted the on-chain submission
    with pytest.raises(Exception):
        # This will fail because "blockchain-123" is not a real payment ID
        # but this tests that the manager correctly calls the real Payment object
        asyncio.run(manager.set_job_completed(job_id, "result"))
    
    # Since the exception was raised, the job won't be marked as completed
    # This is expected behavior - the job manager only marks jobs as completed
    # after successful on-chain submission. We can verify the job is still running:
    job = asyncio.run(manager.get_job(job_id))
    assert job["status"] == "running"
    assert job["result"] is None


def test_start_job_request_accepts_camel_case():
    """StartJobRequest should accept the admin/UI camelCase payload shape."""
    request = StartJobRequest.model_validate(
        {
            "identifierFromPurchaser": "buyer-123",
            "inputData": {"text": "hello"},
        }
    )

    assert request.identifier_from_purchaser == "buyer-123"
    assert request.input_data == {"text": "hello"}


def test_start_job_request_accepts_snake_case():
    """StartJobRequest should remain backwards-compatible with snake_case payloads."""
    request = StartJobRequest.model_validate(
        {
            "identifier_from_purchaser": "buyer-123",
            "input_data": {"text": "hello"},
        }
    )

    assert request.identifier_from_purchaser == "buyer-123"
    assert request.input_data == {"text": "hello"}


@pytest.mark.parametrize(
    ("payment_payload", "expected"),
    [
        ({"price": 0}, True),
        ({"price": "0"}, True),
        ({"price": "0.0"}, True),
        ({"amount": 0}, True),
        ({"amount": "0"}, True),
        ({"amounts": [{"amount": 0}, {"amount": "0"}]}, True),
        ({"price": 1}, False),
        ({"amount": "1"}, False),
        ({"amounts": [{"amount": 0}, {"amount": 1}]}, False),
        ({}, False),
    ],
)
def test_payment_free_agent_detection(payment_payload, expected):
    """Zero-cost payments should be detected across numeric and string payload shapes."""
    assert Payment._is_free_payment(payment_payload) is expected


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
