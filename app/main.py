from io import BytesIO
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.api_models import JobResponse
from app.job_service import JobNotFoundError, JobService
from app.job_store import JobStore


MAX_UPLOAD_BYTES = 5 * 1024 * 1024

SUPPORTED_IMAGE_TYPES = {
    "image/png": ("PNG", ".png"),
    "image/jpeg": ("JPEG", ".jpg"),
}


app = FastAPI(title="ForgeQueue")

job_store = JobStore()
job_service = JobService(job_store)


def get_job_service() -> JobService:
    return job_service


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

    job = service.create_job(input_path)

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