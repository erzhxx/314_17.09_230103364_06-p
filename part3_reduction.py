"""
Part 3: OpenMP-Style Reduction
================================
No shared-state locking at all. Each worker keeps a fully private, local
counter and only returns its partial sum when it's done. The parent process
adds up the partial sums exactly once, after every worker has finished --
conceptually identical to `#pragma omp parallel for reduction(+:totalHits)`.

Benchmarks total wall-clock time for T in {1, 2, 4, 8, 16, 32} workers with
N = 100,000,000 iterations, and prints the Runtime / Speedup / Efficiency
grid requested by the assignment.
"""

import random
import time
from concurrent.futures import ProcessPoolExecutor

TOTAL_POINTS = 100_000_000
THREAD_COUNTS = [1, 2, 4, 8, 16, 32]


def count_hits(args):
    """Fully private work: local RNG, local counter, no shared state at all
    until the single return value is combined by the parent process."""
    points, seed = args
    rng = random.Random(seed)
    local_hits = 0
    for _ in range(points):
        x = rng.random()
        y = rng.random()
        if x * x + y * y <= 1.0:
            local_hits += 1
    return local_hits  # the only thing ever "shared" -- a one-time return value


def split_points(total, num_workers):
    """Split `total` as evenly as possible across `num_workers` chunks."""
    base = total // num_workers
    remainder = total % num_workers
    return [base + (1 if i < remainder else 0) for i in range(num_workers)]


def run_reduction(total_points, num_workers):
    chunks = split_points(total_points, num_workers)
    tasks = [(chunk, i * 999983 + 17) for i, chunk in enumerate(chunks)]

    start = time.perf_counter()
    if num_workers == 1:
        total_hits = count_hits(tasks[0])
    else:
        with ProcessPoolExecutor(max_workers=num_workers) as pool:
            total_hits = sum(pool.map(count_hits, tasks))  # the single reduction step
    elapsed = time.perf_counter() - start

    pi_estimate = 4.0 * total_hits / total_points
    return elapsed, pi_estimate


if __name__ == "__main__":
    print(f"Part 3: OpenMP-Style Reduction -- {TOTAL_POINTS:,} points\n")
    # NOTE: this is a real, full-scale benchmark. On a laptop this can take
    # several minutes end-to-end across all 6 thread counts. Lower
    # TOTAL_POINTS above for a quick local smoke test.

    results = {}
    baseline_time = None

    print(f"{'T':>3} | {'Runtime (ms)':>13} | {'Speedup':>8} | {'Efficiency':>10} | pi")
    print("-" * 55)
    for t in THREAD_COUNTS:
        elapsed, pi_est = run_reduction(TOTAL_POINTS, t)
        results[t] = elapsed
        if t == 1:
            baseline_time = elapsed
        speedup = baseline_time / elapsed
        efficiency = speedup / t
        print(f"{t:>3} | {elapsed * 1000:>13.1f} | {speedup:>7.2f}x | "
              f"{efficiency * 100:>9.1f}% | {pi_est:.6f}")

    print("\nFill these numbers into the README.md table for submission.")
