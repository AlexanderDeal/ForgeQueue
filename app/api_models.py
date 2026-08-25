from uuid import UUID
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import JobStatus


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    input_path: Path
    output_path: Path | None
    error: str | None