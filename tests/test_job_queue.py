from uuid import uuid4

from app.job_queue import InMemoryJobQueue


def test_in_memory_queue_preserves_job_and_attempt() -> None:
    queue = InMemoryJobQueue()
    job_id = uuid4()

    message_id = queue.enqueue(job_id, attempt=2)
    message = queue.dequeue("worker-1")

    assert message is not None
    assert message.message_id == message_id
    assert message.job_id == job_id
    assert message.attempt == 2


def test_in_memory_queue_returns_none_when_empty() -> None:
    assert InMemoryJobQueue().dequeue("worker-1", timeout_ms=0) is None
