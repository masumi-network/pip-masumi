"""
Job state management with pluggable storage interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import uuid
import logging
from .payment import Payment
from .helper_functions import setup_logging

logger = setup_logging(__name__)


class JobStorage(ABC):
    """Abstract base class for job storage backends."""
    
    @abstractmethod
    async def create_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Create a new job entry."""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        pass
    
    @abstractmethod
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update job data."""
        pass
    
    @abstractmethod
    async def delete_job(self, job_id: str) -> None:
        """Delete a job entry."""
        pass
    
    @abstractmethod
    async def list_jobs(self, status: Optional[str] = None) -> list:
        """List all jobs, optionally filtered by status."""
        pass


class InMemoryJobStorage(JobStorage):
    """In-memory job storage implementation (default, for development/testing)."""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized InMemoryJobStorage")
    
    async def create_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Create a new job entry."""
        self._jobs[job_id] = job_data.copy()
        logger.debug(f"Created job {job_id} in memory storage")
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        job = self._jobs.get(job_id)
        if job:
            logger.debug(f"Retrieved job {job_id} from memory storage")
        else:
            logger.debug(f"Job {job_id} not found in memory storage")
        return job.copy() if job else None
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update job data."""
        if job_id in self._jobs:
            self._jobs[job_id].update(updates)
            logger.debug(f"Updated job {job_id} in memory storage")
        else:
            logger.error(f"Attempted to update non-existent job {job_id}")
            raise ValueError(f"Job {job_id} not found in storage")
    
    async def delete_job(self, job_id: str) -> None:
        """Delete a job entry."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.debug(f"Deleted job {job_id} from memory storage")
        else:
            logger.warning(f"Attempted to delete non-existent job {job_id}")
    
    async def list_jobs(self, status: Optional[str] = None) -> list:
        """List all jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [job for job in jobs if job.get("status") == status]
        logger.debug(f"Listed {len(jobs)} jobs (status filter: {status})")
        return jobs


class JobManager:
    """Manages job lifecycle and state tracking."""
    
    def __init__(self, storage: Optional[JobStorage] = None):
        """
        Initialize the job manager.
        
        Args:
            storage: Storage backend (defaults to InMemoryJobStorage)
        """
        self.storage = storage or InMemoryJobStorage()
        self._payment_instances: Dict[str, Payment] = {}
        logger.info("Initialized JobManager")
    
    async def create_job(
        self,
        identifier_from_purchaser: str,
        input_data: Dict[str, Any],
        payment: Payment,
        blockchain_identifier: str,
        pay_by_time: int,
        submit_result_time: int,
        unlock_time: int,
        external_dispute_unlock_time: int,
        agent_identifier: str,
        seller_vkey: str,
        input_hash: Optional[str] = None
    ) -> str:
        """
        Create a new job entry.
        
        Returns:
            str: The generated job ID
        """
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "status": "awaiting_payment",
            "payment_id": blockchain_identifier,
            "identifier_from_purchaser": identifier_from_purchaser,
            "input_data": input_data,
            "pay_by_time": pay_by_time,
            "submit_result_time": submit_result_time,
            "unlock_time": unlock_time,
            "external_dispute_unlock_time": external_dispute_unlock_time,
            "agent_identifier": agent_identifier,
            "seller_vkey": seller_vkey,
            "input_hash": input_hash,
            "result": None,
            "error": None,
            "created_at": None
        }
        
        await self.storage.create_job(job_id, job_data)
        self._payment_instances[job_id] = payment
        
        logger.info(f"Created job {job_id} with status 'awaiting_payment'")
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        return await self.storage.get_job(job_id)
    
    async def update_job_status(self, job_id: str, status: str, **kwargs) -> None:
        """Update job status and optionally other fields."""
        updates = {"status": status, **kwargs}
        await self.storage.update_job(job_id, updates)
        logger.info(f"Updated job {job_id} status to '{status}'")
    
    async def set_job_running(self, job_id: str) -> None:
        """Mark a job as running and confirm payment."""
        await self.update_job_status(
            job_id, 
            "running"
        )
    
    async def set_job_completed(self, job_id: str, result: str) -> None:
        """
        Mark a job as completed with a result and submit it on-chain if applicable.
        
        Args:
            job_id: The job ID
            result: The result string (agent handlers must return strings)
        """
        # Get payment instance and ID for on-chain submission
        payment = self.get_payment_instance(job_id)
        job = await self.get_job(job_id)
        
        if payment and job and job.get("payment_id"):
            payment_id = job.get("payment_id")
            logger.info(f"Submitting result on-chain for job {job_id} (payment ID: {payment_id})")
            logger.info(f"Result length: {len(result)} characters")
            try:
                # This will raise if submission fails, which is intended
                await payment.complete_payment(payment_id, result)
                logger.info(f"Result submitted on-chain successfully for job {job_id}")
            except Exception as e:
                logger.error(f"On-chain result submission FAILED for job {job_id}: {str(e)}")
                raise
        else:
            reason = []
            if not payment: reason.append("payment instance missing")
            if not job: reason.append("job data missing")
            if job and not job.get("payment_id"): reason.append("payment_id missing in job data")
            logger.error(f"SKIPPING on-chain submission for job {job_id}. Reasons: {', '.join(reason)}")

        await self.update_job_status(
            job_id,
            "completed",
            result=result
        )
        logger.info(f"Job {job_id} marked as completed")
    
    async def set_job_failed(self, job_id: str, error: str) -> None:
        """Mark a job as failed with an error message."""
        await self.update_job_status(
            job_id,
            "failed",
            error=error
        )
        logger.error(f"Job {job_id} marked as failed: {error}")
    
    def get_payment_instance(self, job_id: str) -> Optional[Payment]:
        """Get the payment instance for a job."""
        return self._payment_instances.get(job_id)
    
    async def cleanup_payment_instance(self, job_id: str) -> None:
        """Remove payment instance and stop monitoring."""
        payment = self._payment_instances.get(job_id)
        if payment:
            payment.stop_status_monitoring()
            del self._payment_instances[job_id]
            logger.debug(f"Cleaned up payment instance for job {job_id}")
    
    async def list_jobs(self, status: Optional[str] = None) -> list:
        """List all jobs, optionally filtered by status."""
        return await self.storage.list_jobs(status)


