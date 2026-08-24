from enum import Enum
from uuid import UUID, uuid4
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field


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

