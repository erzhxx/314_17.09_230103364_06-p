# Parallel Pi Estimation — Python Version

Solutions to "Part 1: The Phantom Bug", "Part 2: The Synchronization Trap",
and "Part 3: OpenMP-Style Reduction".

## A note on Python vs. the original Java task

The original assignment is written for **Java native threads**. In Python,
plain `threading.Thread` does **not** give real parallelism for CPU-bound
code, because of the Global Interpreter Lock (GIL) — only one thread runs
Python bytecode at a time. If Part 1 were implemented with `threading`, the
race condition would rarely (if ever) actually show up, and you wouldn't see
the intended `pi ≈ 1.8–2.4` bug.

So all three parts use **`multiprocessing`** instead: real OS processes that
run truly concurrently on separate cores, exactly like Java threads do. This
preserves every lesson the assignment is testing for:

| Java concept | Python equivalent used here |
|---|---|
| native `Thread` | `multiprocessing.Process` |
| `static long totalHits; totalHits++;` (no lock) | `multiprocessing.Value('q', 0, lock=False)` |
| `synchronized` / `AtomicLong` | `multiprocessing.Value(lock=True)` + `.get_lock()` |
| thread-local counter + join-time reduction | private local variable + `ProcessPoolExecutor.map` + `sum()` at the end |

## Files

- `part1_phantom_bug.py` — 50,000,000 points, 4 worker processes, **unsynchronized** shared counter. Runs 5 times and prints each π estimate.
- `part2_synchronization_trap.py` — same problem, fixed with a **lock on every increment**, benchmarked against a plain single-process loop.
- `part3_reduction.py` — each worker keeps a **private local counter**; partial sums are combined once at the end. Benchmarks T ∈ {1, 2, 4, 8, 16, 32} with 100,000,000 iterations.

## How to run

```bash
python3 part1_phantom_bug.py
python3 part2_synchronization_trap.py
python3 part3_reduction.py
```

Requires Python 3.8+, no external dependencies. Run each script directly
(not in a notebook) so `multiprocessing` can spawn/fork properly.

**Heads up on runtime:** at full scale (50M / 100M iterations) these are
genuine benchmarks and can take from under a minute to several minutes
depending on your machine, especially Part 2 (the lock-per-increment version
is *deliberately* slow — that's the whole lesson) and Part 3 at T=32. Lower
`TOTAL_POINTS` at the top of each file for quick local smoke-testing.

*(These scripts were smoke-tested in a 1-core sandbox with a reduced point
count to confirm correctness — the race condition in Part 1 reproduces
reliably even on a single core, since the OS can still preempt a process
mid read-modify-write. Run the full-scale versions on your own multi-core
machine to get the real timing numbers below.)*

## Part 3 results (fill in on your machine)

| Threads (T) | Runtime (ms) | Speedup vs. 1 Thread | Efficiency |
|---|---|---|---|
| 1 (baseline) | ... | 1.0x | 100% |
| 2 | ... | ... | ... |
| 4 | ... | ... | ... |
| 8 | ... | ... | ... |
| 16 | ... | ... | ... |
| 32 | ... | ... | ... |

The script prints this table directly — just copy its output in here.

## Questions

**1. Look at your row for 16 threads/processes. Why didn't your 8-core CPU
run twice as fast as 8 threads?**

Once the number of workers exceeds the number of physical cores, extra
workers don't get their own execution unit — they have to time-slice with
existing ones, so the OS scheduler is constantly context-switching between
them instead of doing useful work. On top of that: if the CPU uses
hyperthreading/SMT, "logical" cores beyond the physical count share the same
execution units, caches, and memory bandwidth with their sibling core, so
they can't deliver a full extra core's worth of throughput. Cache contention
also gets worse — more processes means more cache-line evictions and more
traffic on the shared memory bus, which is a resource that doesn't scale up
just because you added more workers. All of this shows up as speedup
flattening out (or even dropping) well before it doubles again, exactly what
Amdahl's Law and real-world oversubscription predict.

**2. Why was the synchronized version in Part 2 slower than running on one
single core?**

Because correctness was bought with constant serialization. Every single
increment has to acquire a lock before touching the shared counter, and with
4 workers hammering the *same* memory location, most of them spend their
time blocked, waiting for the lock instead of computing anything. Each
lock acquire/release also isn't free — it involves atomic CPU instructions
(or, in the multiprocessing/Python case, real OS-level semaphore syscalls),
and the cache line holding the counter has to keep bouncing between cores
each time a different process writes to it ("cache-line ping-ponging"). A
single-threaded loop never pays any of this cost — there's nothing to
synchronize because there's only one execution context. So instead of 4
workers each contributing useful throughput, you get 4 workers mostly
fighting each other over one contended resource, which ends up slower than
doing the whole thing serially on one core.
