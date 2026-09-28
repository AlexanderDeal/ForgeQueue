from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from redis import Redis
from redis.exceptions import ResponseError


@dataclass(frozen=True)
class QueueMessage:
    message_id: str
    job_id: UUID
    attempt: int = 0


class JobQueueProtocol(Protocol):
    def enqueue(self, job_id: UUID, attempt: int = 0) -> str: ...

    def dequeue(self, consumer: str, timeout_ms: int = 5000) -> QueueMessage | None: ...

    def acknowledge(self, message_id: str) -> None: ...

    def recover_stale(
        self, consumer: str, min_idle_ms: int = 60_000
    ) -> QueueMessage | None: ...


class RedisJobQueue:
    def __init__(
        self,
        client: Redis,
        stream: str = "forgequeue:jobs",
        group: str = "forgequeue-workers",
    ) -> None:
        self._client = client
        self._stream = stream
        self._group = group
        try:
            self._client.xgroup_create(stream, group, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def enqueue(self, job_id: UUID, attempt: int = 0) -> str:
        return str(
            self._client.xadd(
                self._stream,
                {"job_id": str(job_id), "attempt": str(attempt)},
            )
        )

    def dequeue(self, consumer: str, timeout_ms: int = 5000) -> QueueMessage | None:
        response = self._client.xreadgroup(
            self._group,
            consumer,
            {self._stream: ">"},
            count=1,
            block=timeout_ms,
        )
        if not response:
            return None
        _, messages = response[0]
        message_id, fields = messages[0]
        return QueueMessage(
            message_id=str(message_id),
            job_id=UUID(str(fields["job_id"])),
            attempt=int(fields.get("attempt", 0)),
        )

    def acknowledge(self, message_id: str) -> None:
        self._client.xack(self._stream, self._group, message_id)

    def recover_stale(
        self, consumer: str, min_idle_ms: int = 60_000
    ) -> QueueMessage | None:
        response = self._client.xautoclaim(
            self._stream,
            self._group,
            consumer,
            min_idle_ms,
            "0-0",
            count=1,
        )
        messages = response[1]
        if not messages:
            return None
        message_id, fields = messages[0]
        return QueueMessage(
            message_id=str(message_id),
            job_id=UUID(str(fields["job_id"])),
            attempt=int(fields.get("attempt", 0)),
        )


class InMemoryJobQueue:
    def __init__(self) -> None:
        self.messages: list[QueueMessage] = []

    def enqueue(self, job_id: UUID, attempt: int = 0) -> str:
        message_id = str(len(self.messages) + 1)
        self.messages.append(QueueMessage(message_id, job_id, attempt))
        return message_id

    def dequeue(self, consumer: str, timeout_ms: int = 5000) -> QueueMessage | None:
        del consumer, timeout_ms
        return self.messages.pop(0) if self.messages else None

    def acknowledge(self, message_id: str) -> None:
        del message_id

    def recover_stale(
        self, consumer: str, min_idle_ms: int = 60_000
    ) -> QueueMessage | None:
        del consumer, min_idle_ms
        return None
