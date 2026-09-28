# ForgeQueue

ForgeQueue is a distributed image-processing platform built to demonstrate
backend engineering fundamentals: API design, durable state, message queues,
independent workers, retries, containers, cloud storage boundaries, CI, and
performance measurement.

## Architecture

```text
Client
  -> FastAPI API
      -> PostgreSQL (durable job metadata and state)
      -> Redis Stream (job IDs and delivery attempts)
  -> Worker pool
      -> shared local volume today / S3 adapter for cloud deployment
      -> PostgreSQL status updates
```

PostgreSQL is the source of truth. Redis is delivery infrastructure: queue
messages contain a job UUID and retry attempt, not a serialized domain object.
Workers use a consumer group, so multiple processes divide work. A message is
acknowledged only after processing; stale pending messages can be reclaimed
after a worker crash.

## Job lifecycle

`PENDING -> QUEUED -> PROCESSING -> COMPLETED`

Failures move a job to `FAILED`. Retryable failures move through
`FAILED -> RETRYING -> QUEUED` before another delivery attempt. The worker uses
bounded exponential backoff and a configurable maximum attempt count.

## Run locally with Docker

Docker Desktop (or Docker Engine with Compose) is the only prerequisite.

```powershell
docker compose up --build
```

Open <http://127.0.0.1:8000/docs>. Compose starts PostgreSQL, Redis, runs
Alembic migrations, starts the API, and starts two worker replicas. Uploaded
and processed files live in a named shared volume.

Scale workers independently:

```powershell
docker compose up --scale worker=4
```

Stop services while retaining data with `docker compose down`. Add `-v` only
when you intentionally want to delete database, Redis, and media volumes.

## Run without Docker

Set the variables shown in `.env.example`, apply migrations, then run the API,
Redis, and at least one worker:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app
python -m app.worker
```

## Tests and benchmark

```powershell
python -m pytest
python scripts/benchmark.py sample.png --requests 100 --concurrency 20
```

Benchmark API submission latency separately from end-to-end processing time.
Compare identical workloads with different Compose worker counts and report the
actual throughput, mean latency, and p95 latency.

## AWS path

`S3ObjectStorage` supplies upload, download, and short-lived presigned result
URLs. A production deployment would use ECR for the same Docker image, ECS for
API/worker services, RDS PostgreSQL, ElastiCache Redis, and S3 media storage.
No cloud resources are created by this repository. Prefer IAM task roles over
long-lived AWS keys and set billing alerts before deployment.

## Reliability boundaries

- PostgreSQL and Redis cannot share one atomic transaction. A production-scale
  next step is a transactional outbox to eliminate the DB/queue publication
  gap.
- Redis Stream pending entries support crash recovery, but poison messages need
  a dead-letter stream for long-term operations.
- Local media storage requires a shared volume; S3 removes that coupling in a
  multi-host deployment.
