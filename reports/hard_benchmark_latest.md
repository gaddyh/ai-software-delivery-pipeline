# Hard Benchmark — Latest Run

Batch run executed on 2026-05-18 using the failure-aware routing pipeline.

Pipeline version includes: structured failure analysis, artifact-level repair routing (implementation repair, test syntax repair, test grounding review), and Code Quality Critic gating.

## Results

| # | Task | Run ID | Result | Iterations | What it exposed |
|---|------|--------|-------:|----------:|-----------------|
| 1 | `calculate_coupon_discount` | `20260518_191813` | ✓ Passed | 1 | First-pass success. Caps, rule ordering, and 25% discount cap handled correctly. |
| 2 | `LoginAttemptTracker` | `20260518_191826` | ✓ Passed | 1 | First-pass success. Lock behavior and reset logic handled correctly. |
| 3 | `OrderStateMachine` | `20260518_191845` | ✓ Passed | 2 | Iteration 1: `list_orders_by_status` returned insertion order instead of alphabetical sort. Failure analyzer classified as `assertion_mismatch` blamed on `implementation`. Repaired in iteration 2. |
| 4 | `RoomBooking` | `20260518_191914` | ✓ Passed | 1 | First-pass success. Interval overlap logic, back-to-back bookings, and exact cancellation handled correctly. Previously exposed a test-grounding issue in earlier runs (test expected room name in `get_bookings` output; spec declares `list[tuple[int, int]]`). Now generates correctly grounded tests. |
| 5 | `BudgetAllocator` | `20260518_191935` | ✓ Passed | 1 | First-pass success. Over-budget allocation raises ValueError; reset category sets to 0.0. |

**Pass rate: 5/5**

## Routing Activity

| Task | Repair Route Triggered | Times |
|------|----------------------|------:|
| calculate_coupon_discount | none | 0 |
| LoginAttemptTracker | none | 0 |
| OrderStateMachine | implementation repair | 1 |
| RoomBooking | none | 0 |
| BudgetAllocator | none | 0 |

## Failure Detail — OrderStateMachine Iteration 1

```
test_list_orders_by_status_sorts_order_ids

AssertionError: assert ['order123', 'order001', 'order002'] == ['order001', 'order002', 'order123']
  At index 0 diff: 'order123' != 'order001'

failure_type    : assertion_mismatch
blamed_artifact : implementation
confidence      : 0.9
routing         : → Developer Agent (implementation repair)
```

The initial implementation returned orders in insertion order. The repair added `sorted()` to `list_orders_by_status`.

## Notes

- All 5 tasks used the `harder_mvp1_benchmark_set` from `benchmark_user_messages.py`
- Artifacts for each run are stored under `artifacts/runs/{run_id}/` (gitignored; inspect locally)
- Each `failure_analysis_iterN.json` contains the full structured routing decision
- This benchmark is not presented as a solved system. It is used to expose failure modes and verify routing behavior under executable feedback.
