import argparse
import concurrent.futures
import statistics
import time
from pathlib import Path
from uuid import UUID

import httpx


def submit_and_wait(base_url: str, image_path: Path, timeout: float) -> float:
    started = time.perf_counter()
    media_type = (
        "image/jpeg"
        if image_path.suffix.lower() in {".jpg", ".jpeg"}
        else "image/png"
    )
    with httpx.Client(timeout=30) as client:
        with image_path.open("rb") as image:
            response = client.post(
                f"{base_url}/jobs",
                files={"uploaded_file": (image_path.name, image, media_type)},
            )
        response.raise_for_status()
        job_id = UUID(response.json()["id"])

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status_response = client.get(f"{base_url}/jobs/{job_id}")
            status_response.raise_for_status()
            status = status_response.json()["status"]
            if status == "COMPLETED":
                return time.perf_counter() - started
            if status == "FAILED":
                raise RuntimeError(f"job {job_id} failed")
            time.sleep(0.05)

    raise TimeoutError(f"job {job_id} did not complete within {timeout}s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--workers", type=int, required=True)
    args = parser.parse_args()

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(args.concurrency) as executor:
        latencies = list(
            executor.map(
                lambda _: submit_and_wait(args.url, args.image, args.timeout),
                range(args.requests),
            )
        )
    elapsed = time.perf_counter() - started
    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    print(f"requests={args.requests}")
    print(f"workers={args.workers}")
    print(f"end_to_end_throughput={args.requests / elapsed:.2f} jobs/s")
    print(f"mean_end_to_end_latency={statistics.mean(latencies):.3f}s")
    print(f"p95_end_to_end_latency={p95:.3f}s")


if __name__ == "__main__":
    main()
