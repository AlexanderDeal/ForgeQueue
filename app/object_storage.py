from pathlib import Path
from typing import Protocol

from boto3.session import Session


class ObjectStorageProtocol(Protocol):
    def upload(self, source: Path, key: str) -> None: ...

    def download(self, key: str, destination: Path) -> None: ...

    def result_url(self, key: str, expires_seconds: int = 900) -> str: ...


class S3ObjectStorage:
    def __init__(
        self,
        bucket: str,
        region: str | None = None,
        session: Session | None = None,
    ) -> None:
        self._bucket = bucket
        self._client = (session or Session()).client("s3", region_name=region)

    def upload(self, source: Path, key: str) -> None:
        self._client.upload_file(str(source), self._bucket, key)

    def download(self, key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(self._bucket, key, str(destination))

    def result_url(self, key: str, expires_seconds: int = 900) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )
