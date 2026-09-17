

import multiprocessing as mp
import random
import time

TOTAL_POINTS = 500_000
NUM_WORKERS = 4


# ---------------------------------------------------------------------------
# Single-threaded baseline (no synchronization needed -- only one execution
# context ever touches the counter)
# ---------------------------------------------------------------------------
def single_threaded_pi(points):
    rng = random.Random(12345)
    hits = 0
    for _ in range(points):
        x = rng.random()
        y = rng.random()
        if x * x + y * y <= 1.0:
            hits += 1
    return 4.0 * hits / points


# ---------------------------------------------------------------------------
# Synchronized / locked multiprocessing version
# ---------------------------------------------------------------------------
def locked_worker(shared_hits, points, seed):
    rng = random.Random(seed)
    for _ in range(points):
        x = rng.random()
        y = rng.random()
        if x * x + y * y <= 1.0:
            # Every single hit takes the lock -- deliberately worst-case,
            # this is the direct analogue of `synchronized` around
            # `totalHits++` in Java.
            with shared_hits.get_lock():
                shared_hits.value += 1


def locked_pi(total_points, num_workers):
    shared_hits = mp.Value('q', 0, lock=True)  # lock=True -> real synchronization
    points_per_worker = total_points // num_workers
    procs = []
    for i in range(num_workers):
        seed = i * 104729 + 1
        p = mp.Process(target=locked_worker, args=(shared_hits, points_per_worker, seed))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
    return 4.0 * shared_hits.value / total_points


if __name__ == "__main__":
    print(f"Part 2: Synchronization Trap -- {TOTAL_POINTS:,} points\n")

    # NOTE: the locked version below acquires an inter-process lock on every
    # single hit (~39M times for 50M points). That is intentionally
    # pathological -- it is the whole point of the exercise -- but it can
    # take a while. Lower TOTAL_POINTS above for a quicker local test run.

    print("Running single-threaded baseline...")
    t0 = time.perf_counter()
    pi_single = single_threaded_pi(TOTAL_POINTS)
    t_single = time.perf_counter() - t0
    print(f"  pi = {pi_single:.6f}   time = {t_single:.2f}s")

    print(f"\nRunning synchronized version ({NUM_WORKERS} workers, lock per increment)...")
    t0 = time.perf_counter()
    pi_locked = locked_pi(TOTAL_POINTS, NUM_WORKERS)
    t_locked = time.perf_counter() - t0
    print(f"  pi = {pi_locked:.6f}   time = {t_locked:.2f}s")

    print("\n--- Comparison ---")
    print(f"Single-threaded : {t_single:.2f}s  (correct pi, no locking overhead)")
    print(f"Synchronized    : {t_locked:.2f}s  (correct pi, but "
          f"{t_locked / t_single:.1f}x slower than single-threaded)")
    print("\nExpected: the synchronized version is ACCURATE (~3.14159) but "
          "drastically slower than the single-threaded loop, because every "
          "worker is constantly blocking/waking up to fight over the same "
          "lock instead of doing useful work.")
