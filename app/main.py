from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException

from app.api_models import JobResponse
from app.job_service import JobNotFoundError, JobService
from app.job_store import JobStore


app = FastAPI(title="ForgeQueue")

job_store = JobStore()
job_service = JobService(job_store)


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


def get_job_service() -> JobService:
    return job_service


@app.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(
    job_id: UUID,
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobResponse:
    try:
        job = service.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return JobResponse.model_validate(job)