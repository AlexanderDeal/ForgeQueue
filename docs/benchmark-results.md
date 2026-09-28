# Local Benchmark Results

Measured on September 28, 2026 with Docker Desktop on the development machine.
Each run submitted 30 copies of the same 2.8 MB, 2400×1600 JPEG with concurrency
10 and measured the complete interval from upload through `COMPLETED` status.

| Workers | Throughput | Mean latency | p95 latency |
| ---: | ---: | ---: | ---: |
| 1 | 28.87 jobs/s | 0.310 s | 0.520 s |
| 2 | 40.30 jobs/s | 0.228 s | 0.363 s |
| 4 | 41.14 jobs/s | 0.223 s | 0.344 s |

Moving from one to two workers increased throughput by approximately 40% and
reduced mean latency by approximately 26%. Four workers produced little further
gain, indicating that this workload reached another local bottleneck such as
CPU contention, upload/HTTP overhead, database access, Redis coordination, or
polling frequency. These results describe this machine and workload only; they
are not universal capacity claims.

The benchmark is reproducible with `scripts/benchmark.py`. Future comparisons
should preserve the input image, request count, concurrency, and host resources.
