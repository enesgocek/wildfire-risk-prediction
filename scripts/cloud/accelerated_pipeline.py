"""Bounded day graph: pairs, a serialized publisher and independent daily children.

All scientific callbacks run in the main thread; frozen science modules use
mutable ROOT globals and must never be invoked concurrently in threads.
"""

import concurrent.futures as cf
import time
from collections import deque


def execute(
    days,
    prepare,
    launch_pair,
    publish_pair,
    launch_day,
    publish_day,
    pair_slots,
    day_slots,
    deadline,
    healthy,
    stop_children,
    reserve=1200,
    window=4,
):
    if not (1 <= pair_slots <= 24 and 1 <= day_slots <= 4 and 1 <= window <= 6):
        raise ValueError("Pipeline bounds")
    states, pair_jobs, day_jobs = {}, {}, {}
    pending, ready_pairs, ready_days, reducible = deque(), deque(), deque(), deque()
    results = {}
    exhausted, draining = False, False
    source = iter(days)

    def admission():
        return healthy() and time.monotonic() + reserve < deadline

    def finish(state, record):
        identity = state["day"]
        if identity in results:
            raise ValueError("Duplicate daily completion")
        results[identity] = record
        states.pop(identity)

    def daily_ready(state):
        if state["remaining"] == 0 and not state.get("reduction_queued"):
            state["reduction_queued"] = True
            reducible.append(state)

    with (
        cf.ThreadPoolExecutor(max_workers=pair_slots) as pair_pool,
        cf.ThreadPoolExecutor(max_workers=day_slots) as day_pool,
    ):
        try:
            while True:
                if not healthy() or time.monotonic() >= deadline:
                    raise TimeoutError("Pipeline resource/deadline guard")
                if not admission():
                    draining = True
                while not exhausted and not draining and len(states) < window:
                    if not admission():
                        draining = True
                        break
                    identity = next(source, None)
                    if identity is None:
                        exhausted = True
                        break
                    state = prepare(identity)
                    if state["day"] != identity or identity in states or identity in results:
                        raise ValueError("Day graph identity")
                    states[identity] = state
                    if state.get("reused") is not None:
                        finish(state, state["reused"])
                        continue
                    state["remaining"] = len(state["pending"])
                    pending.extend((state, pair) for pair in state["pending"])
                    daily_ready(state)
                while (
                    pending
                    and not draining
                    and len(pair_jobs) < pair_slots
                    and len(ready_pairs) < pair_slots
                ):
                    state, pair = pending.popleft()
                    future = pair_pool.submit(launch_pair, state, pair)
                    pair_jobs[future] = (state, pair)
                while reducible and not draining and len(day_jobs) < day_slots:
                    state = reducible.popleft()
                    day_jobs[day_pool.submit(launch_day, state)] = state
                jobs = {*pair_jobs, *day_jobs}
                if jobs:
                    done, _ = cf.wait(
                        jobs,
                        timeout=0 if ready_pairs or ready_days else 1,
                        return_when=cf.FIRST_COMPLETED,
                    )
                    for future in done:
                        value = future.result()
                        if future in pair_jobs:
                            state, pair = pair_jobs.pop(future)
                            ready_pairs.append((state, pair, value))
                        else:
                            ready_days.append((day_jobs.pop(future), value))
                    # Refill freed slots before any blocking scientific/Drive publication.
                    while (
                        pending
                        and not draining
                        and len(pair_jobs) < pair_slots
                        and len(ready_pairs) < pair_slots
                    ):
                        state, pair = pending.popleft()
                        pair_jobs[pair_pool.submit(launch_pair, state, pair)] = (state, pair)
                if ready_days:
                    state, value = ready_days.popleft()
                    finish(state, publish_day(state, value))
                elif ready_pairs:
                    state, pair, value = ready_pairs.popleft()
                    publish_pair(state, pair, value)
                    state["remaining"] -= 1
                    daily_ready(state)
                elif not jobs:
                    if draining or (exhausted and not states):
                        break
                    if reducible or pending:
                        continue
                    raise RuntimeError("Day graph stalled")
            return {
                "status": "complete" if exhausted and not states else "paused_at_runtime_reserve",
                "day_records": results,
                "incomplete_days": sorted(states),
            }
        except BaseException:
            stop_children()
            for future in [*pair_jobs, *day_jobs]:
                future.cancel()
            raise
