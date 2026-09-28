import argparse
import concurrent.futures
import statistics
import time
from pathlib import Path

import httpx


def submit(base_url: str, image_path: Path) -> float:
    started = time.perf_counter()
    with image_path.open("rb") as image:
        response = httpx.post(
            f"{base_url}/jobs",
            files={"uploaded_file": (image_path.name, image, "image/png")},
            timeout=30,
        )
    response.raise_for_status()
    return time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(args.concurrency) as executor:
        latencies = list(
            executor.map(
                lambda _: submit(args.url, args.image),
                range(args.requests),
            )
        )
    elapsed = time.perf_counter() - started
    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    print(f"requests={args.requests}")
    print(f"throughput={args.requests / elapsed:.2f} requests/s")
    print(f"mean_latency={statistics.mean(latencies):.3f}s")
    print(f"p95_latency={p95:.3f}s")


if __name__ == "__main__":
    main()
