from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError

from app.api_models import JobResponse
from app.database import create_database_engine
from app.database_job_store import DatabaseJobStore
from app.job_service import JobNotFoundError, JobService
from app.models import JobStatus


MAX_UPLOAD_BYTES = 5 * 1024 * 1024

SUPPORTED_IMAGE_TYPES = {
    "image/png": ("PNG", ".png"),
    "image/jpeg": ("JPEG", ".jpg"),
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_database_engine()
    job_store = DatabaseJobStore(engine)
    job_service = JobService(job_store)
    app.state.job_service = job_service

    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="ForgeQueue", lifespan=lifespan)


def get_job_service(request: Request) -> JobService:
    return request.app.state.job_service


def get_result_dir() -> Path:
    return Path("storage/results")


def get_upload_dir() -> Path:
    return Path("storage/uploads")


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    uploaded_file: Annotated[UploadFile, File(...)],
    service: Annotated[JobService, Depends(get_job_service)],
    upload_dir: Annotated[Path, Depends(get_upload_dir)],
    result_dir: Annotated[Path, Depends(get_result_dir)],
    background_tasks: BackgroundTasks,
) -> JobResponse:
    expected_type = SUPPORTED_IMAGE_TYPES.get(uploaded_file.content_type)
    if expected_type is None:
        raise HTTPException(
            status_code=415,
            detail="Only PNG and JPEG images are supported",
        )

    contents = await uploaded_file.read(MAX_UPLOAD_BYTES + 1)

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the 5 MB limit",
        )

    try:
        with Image.open(BytesIO(contents)) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image",
        ) from exc

    expected_format, extension = expected_type
    if image_format != expected_format:
        raise HTTPException(
            status_code=400,
            detail="Declared content type does not match the image bytes",
        )

    upload_dir.mkdir(parents=True, exist_ok=True)

    input_path = upload_dir / f"{uuid4()}{extension}"
    input_path.write_bytes(contents)

    try:
        job = service.create_job(input_path)
    except Exception:
        input_path.unlink(missing_ok=True)
        raise

    result_dir.mkdir(parents=True, exist_ok=True)
    output_path = result_dir / f"{job.id}{extension}"

    background_tasks.add_task(
        service.process_job,
        job.id,
        output_path,
        (200, 200),
    )

    return JobResponse.model_validate(job)


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


@app.get("/jobs/{job_id}/result", response_class=FileResponse)
def read_result(
    job_id: UUID,
    service: Annotated[JobService, Depends(get_job_service)],
) -> FileResponse:
    try:
        job = service.get_job(job_id)
        if job.status is not JobStatus.COMPLETED or job.output_path is None:
            raise HTTPException(status_code=409, detail="Job result is not ready")
        if not job.output_path.is_file():
            raise HTTPException(status_code=404, detail="Result file not found",)

    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(path=job.output_path, filename=job.output_path.name)
