from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4


class JobStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    
@dataclass
class Job:
    input_path: Path
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    output_path: Path | None = None
    error: str | None = None

    def transition_to(self, new_status: JobStatus) -> None:
        valid_transitions = {
            JobStatus.PENDING: {JobStatus.PROCESSING},
            JobStatus.PROCESSING: {JobStatus.COMPLETED, JobStatus.FAILED},
            JobStatus.COMPLETED: set(),
            JobStatus.FAILED: set(),
        }

        if new_status not in valid_transitions[self.status]:
            raise InvalidJobTransitionError(self.status, new_status)

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)


class InvalidJobTransitionError(Exception):
    def __init__(self, current_status: JobStatus, requested_status: JobStatus) -> None:
        self.current_status = current_status
        self.requested_status = requested_status
        super().__init__(
            f"Invalid status transition, current status: {self.current_status}, "
            f"requested_status: {self.requested_status}"
        )