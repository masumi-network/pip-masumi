"""
Human-in-the-loop (HITL) utilities for Masumi agents.

This module provides helper functions for agents to request human input
during job execution, pausing execution until input is provided.
"""

import asyncio
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable to store current job execution context
_job_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('job_context', default=None)

# Dictionary to store async events for waiting on input
# Key: job_id, Value: asyncio.Event that will be set when input arrives
_input_events: Dict[str, asyncio.Event] = {}

# Dictionary to store input data when it arrives
# Key: job_id, Value: input_data dict
_input_data_store: Dict[str, Dict[str, Any]] = {}


async def request_input(input_schema: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
    """
    Request human input during job execution.
    
    This pauses execution, sets job status to AWAITING_INPUT, and waits for input
    to be provided via the /provide_input endpoint.
    
    Args:
        input_schema: Schema defining what input is needed (MIP-003 format)
        message: Optional message explaining why input is needed
    
    Returns:
        Dict containing the provided input data
    
    Raises:
        RuntimeError: If called outside of a job execution context
        asyncio.TimeoutError: If input is not provided within timeout (if implemented)
    """
    context = _job_context.get()
    if not context:
        raise RuntimeError("request_input() can only be called during job execution")
    
    job_id = context['job_id']
    job_manager = context['job_manager']
    
    # Create an event for this job BEFORE updating status to avoid race condition
    # If we update status first, a client could poll /status, see awaiting_input,
    # and call /provide_input before the event exists, causing indefinite wait
    if job_id not in _input_events:
        _input_events[job_id] = asyncio.Event()
    else:
        # Reset the event in case it was already set
        _input_events[job_id].clear()
    
    # Set job to awaiting input status (after event is ready)
    await job_manager.set_job_awaiting_input(job_id, input_schema, message)
    
    # Wait for input via async event
    # This will block until provide_input is called and sets the event
    await _input_events[job_id].wait()
    
    # Retrieve the input data
    input_data = _input_data_store.pop(job_id, {})
    
    # Clean up the event
    _input_events.pop(job_id, None)
    
    return input_data


def set_job_context(job_id: str, job_manager: Any) -> None:
    """
    Set the current job context for HITL functionality.
    
    This should be called by the server before executing process_job.
    
    Args:
        job_id: The current job ID
        job_manager: The JobManager instance
    """
    _job_context.set({
        'job_id': job_id,
        'job_manager': job_manager
    })


def clear_job_context() -> None:
    """Clear the current job context."""
    _job_context.set(None)


def provide_input_to_job(job_id: str, input_data: Dict[str, Any]) -> None:
    """
    Provide input to a job that is waiting for input.
    
    This should be called by the provide_input handler when input arrives.
    
    Args:
        job_id: The job ID waiting for input
        input_data: The input data to provide
    """
    # Store the input data
    _input_data_store[job_id] = input_data
    
    # Signal the waiting coroutine
    if job_id in _input_events:
        _input_events[job_id].set()
