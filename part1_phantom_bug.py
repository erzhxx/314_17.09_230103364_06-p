import multiprocessing as mp
import random
import time

# ---- Tunables -------------------------------------------------------------
TOTAL_POINTS = 50_000_000      # as specified in the assignment
NUM_WORKERS = 4                # 4 "threads" -> 4 worker processes
RUNS = 5
# -----------------------------------------------------------------------------

POINTS_PER_WORKER = TOTAL_POINTS // NUM_WORKERS


def worker(shared_hits, points, seed):
    """Each worker does its own dart-throwing, then racily adds its local
    total onto the shared counter ONE INCREMENT AT A TIME, exactly like
    `totalHits++` being called in a loop -- this is what creates the race."""
    rng = random.Random(seed)
    local_hits = 0
    for _ in range(points):
        x = rng.random()
        y = rng.random()
        if x * x + y * y <= 1.0:
            local_hits += 1

    # THE BUG lives here: no lock at all around a shared read-modify-write.
    for _ in range(local_hits):
        shared_hits.value += 1


def run_once():
    shared_hits = mp.Value('q', 0, lock=False)  # lock=False -> no synchronization
    procs = []
    for i in range(NUM_WORKERS):
        seed = i * 104729 + int(time.time_ns() % 1_000_000)
        p = mp.Process(target=worker, args=(shared_hits, POINTS_PER_WORKER, seed))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()

    pi_estimate = 4.0 * shared_hits.value / TOTAL_POINTS
    return pi_estimate, shared_hits.value


if __name__ == "__main__":
    print(f"Part 1: Phantom Bug -- {TOTAL_POINTS:,} points, {NUM_WORKERS} workers, "
          f"UNSYNCHRONIZED shared counter\n")
    print(f"{'Run':>4} | {'hits (racy)':>14} | {'pi estimate':>12}")
    print("-" * 38)
    for run in range(1, RUNS + 1):
        start = time.perf_counter()
        pi_est, hits = run_once()
        elapsed = time.perf_counter() - start
        print(f"{run:>4} | {hits:>14,} | {pi_est:>12.6f}   ({elapsed:.2f}s)")

    print("\nExpected: pi estimates come out noticeably below 3.14159 "
          "(often ~1.8-2.9) and are DIFFERENT on every run -- lost increments "
          "from the race condition, not measurement noise.")
