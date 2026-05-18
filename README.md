# AI Software Delivery Pipeline

An evaluation-driven AI engineering project that generates Python code, executes real pytest suites, classifies failures by responsible artifact, and routes repair to the right agent.

This is not a one-shot codegen demo. It is a measurable artifact-generation loop for studying how AI software systems fail and recover.

The system converts a natural language software requirement into executable artifacts:

```text
Requirement
→ Structured Spec
→ Pytest Suite
→ Generated Code
→ Real Execution
→ Failure Analysis
→ Repair Routing
   ├── Implementation Repair
   ├── Test Suite Repair
   └── Test Grounding Review
→ Quality Critique
→ Engineering Report
```

The system uses executable pytest feedback, structured failure classification, and artifact-aware repair routing to improve generated code reliability over multiple iterations.

Unlike one-shot code generation demos, this project classifies failures by responsible artifact — implementation, test suite, or spec/test expectation — and routes repair accordingly.

---

[Benchmark](#benchmark-results) · [Architecture](#architecture) · [Walkthrough](#example-walkthrough) · [What This Proves](#what-this-project-proves) · [Known Limitations](#known-limitations) · [Next Milestones](#next-engineering-milestones)

---

## Reviewer Path

If you only have 2 minutes:

1. Read [Failure-Aware Repair Routing](#failure-aware-repair-routing)
2. Check [Latest Hard Benchmark](#latest-hard-benchmark) — full report at [`reports/hard_benchmark_latest.md`](reports/hard_benchmark_latest.md)
3. Read a curated run report: [`reports/example_run_report.md`](reports/example_run_report.md)
4. Inspect `failure_analysis_iterN.json` in any run directory to see artifact-level routing

---

## Why This Matters

LLM-generated code is probabilistic.

Execution results are factual.

This project explores how executable feedback loops can make AI software systems more reliable by grounding refinement in real pytest execution instead of relying solely on probabilistic self-correction.

---

## Design Principles

- Artifacts over conversations
- Execution over self-reflection
- Fixed tests during repair loops
- Explicit failure analysis
- Observable iteration history
- Quality gates after passing tests

---

## Benchmark Results

### MVP Benchmark Suite A

Batch run executed on 2026-05-12 using 5 progressive tasks:

| # | Task | Status | Iterations |
|---|------|--------|------------|
| 1 | apply_discount (function) | ✓ Passed | 2 |
| 2 | calculate_ticket_price (function) | ✓ Passed | 1 |
| 3 | BankAccount (class) | ✓ Passed | 1 |
| 4 | Inventory (class) | ✓ Passed | 1 |
| 5 | GradeBook (class) | ✓ Passed | 1 |

**100% task convergence (5/5)**

| Metric | Value |
|--------|-------|
| Tasks | 5 |
| Convergence Rate | 100% |
| First-pass Success | 80% |
| Avg Iterations | 1.2 |
| Avg Repair Iterations | 0.2 |
| Critic Rejections | 0 |

### Latest Hard Benchmark

Batch run on 2026-05-18 using the failure-aware routing pipeline (`harder_mvp1_benchmark_set`, 5 tasks).

Full report: [`reports/hard_benchmark_latest.md`](reports/hard_benchmark_latest.md)

| Task | Result | Iterations | What it exposed |
|------|-------:|----------:|---|
| calculate_coupon_discount | ✓ Passed | 1 | First-pass success. Caps, rule ordering, and 25% discount cap handled correctly. |
| LoginAttemptTracker | ✓ Passed | 1 | First-pass success. Lock behavior and reset logic handled correctly. |
| OrderStateMachine | ✓ Passed | 2 | Iteration 1: `list_orders_by_status` returned insertion order. Classified as `assertion_mismatch / implementation`. Repaired in iteration 2. |
| RoomBooking | ✓ Passed | 1 | First-pass success. Previously exposed test-grounding issue — now generates correctly grounded tests. |
| BudgetAllocator | ✓ Passed | 1 | First-pass success. Over-budget allocation and reset constraints handled correctly. |

**Pass rate: 5/5**

This benchmark is not presented as a solved system. It is used to verify routing behavior, expose failure modes, and measure the effect of pipeline changes under executable feedback.

### Failure Categories Observed

- Floating-point precision edge cases
- Rule-ordering mistakes (tier/modifier application sequence)
- String-constant inconsistencies (spelling variants)
- Missing edge-case validation
- Incorrect state transitions

These failure categories emerged from real execution traces during iterative refinement and were later used to improve repair-mode behavior.

---

## Architecture

```text
User Requirement
      ↓
Orchestrator Agent → TaskSpec
      ↓
Tester Agent → Initial Pytest Suite
      ↓
Developer Agent → Initial Code
      ↓
Pytest Runner
      ↓
Failure Analyzer
      ↓
Repair Router
 ├── implementation bug ──────────→ Developer Agent
 ├── test collection error ───────→ TesterAgent.repair_tests
 ├── ungrounded test expectation ──→ TesterAgent.review_and_repair_test_grounding
 └── pass ───────────────────→ Quality Critic
                                          ↓
                                      Run Report
```

The initial test suite is fixed during implementation repair. The Tester Agent is only called again when the failure analyzer attributes the problem to the test artifact itself — such as collection errors or ungrounded test expectations.

---

## Failure-Aware Repair Routing

The first version of the pipeline treated every pytest failure as an implementation bug.

Harder benchmark runs exposed that this was wrong. Some failures came from generated test suites, not generated code.

| Failure Type | Responsible Artifact | Route |
|---|---|---|
| `test_syntax_error` | test suite | `TesterAgent.repair_tests` |
| `test_indentation_error` | test suite | `TesterAgent.repair_tests` |
| `test_import_error` | test suite | `TesterAgent.repair_tests` |
| `numeric_precision` | implementation | minimal developer repair |
| `assertion_mismatch` | implementation | developer repair |
| `spec_test_conflict` | test expectation / spec | `TesterAgent.review_and_repair_test_grounding` |
| `test_expectation_not_grounded` | test suite | `TesterAgent.review_and_repair_test_grounding` |

Routing priority (defensive ordering in `run.py`):

1. `should_review_spec AND should_modify_tests` → test grounding review (max 1 attempt)
2. `should_modify_tests AND NOT should_modify_code` → test syntax/collection repair (max 2 attempts)
3. `should_modify_code` → implementation repair
4. else → stop

This prevents wasting all repair iterations on the wrong artifact.

---

## What Changed During Development

1. **Naive repair loop** — Every failure was sent to the Developer Agent.

2. **Structured failure analysis** — Pytest output was converted into normalized failure types and routing hints via a schema-enforced LLM call.

3. **Failure-aware routing** — Test-suite failures were routed to the Tester Agent instead of wasting implementation repair iterations.

4. **Test grounding review** — Some valid pytest failures were recognized as possible test/spec conflicts rather than pure implementation bugs. The system checks whether the test's expected value is consistent with the spec's declared return type before modifying anything.

---

## What This Project Proves

| Skill | How it's implemented |
|-------|----------------------|
| Structured output modeling | Pydantic models for TaskSpec, ExecutionResult, FailureAnalysis, QualityReport |
| Agent role separation | Distinct orchestrator, tester, developer, failure analyzer, and critic agents |
| Test-driven code generation | Fixed pytest suite generated from spec before any code is written |
| Iterative repair loops | Developer agent refines code from failure traces, up to N iterations |
| Failure trace analysis | Structured diagnosis of pytest output before re-prompting |
| Quality gating | Critic reviews passing code for overfitting and rule violations |
| Artifact-based engineering | Every run produces inspectable JSON and Python file artifacts |
| Run-level observability | Full iteration history and engineering report per run |
| Evaluation-driven development | Benchmark suite with convergence metrics across task categories |
| Failure attribution | The system decides whether the responsible artifact is implementation, test suite, or spec/test expectation |
| Repair routing | Different failure types route to different agents instead of always rewriting code |
| Test-suite repair | Collection errors such as syntax or indentation failures are repaired by the Tester Agent |
| Test grounding review | The system can detect when a test expectation may not be supported by the original spec |

---

## Run Artifacts

Each execution produces a versioned artifact directory under `artifacts/runs/{run_id}/`:

- Structured task specification (`task_spec.json`)
- Generated pytest suite (`test_suite.py`)
- Generated implementation per iteration (`generated_code_iterN.py`)
- Execution traces per iteration (`execution_result_iterN.json`)
- Failure analyses per iteration (`failure_analysis_iterN.json`)
- Quality reports after passing iterations (`quality_report_iterN.json`)
- Final engineering report (`run_report.md`)

---

## Screenshots

![Benchmark run](assets/screenshots/benchmark_run.png)
![Artifact folder](assets/screenshots/artifact_folder.png)
![Run report](assets/screenshots/run_report.png)

*Screenshots from run `20260512_115150`.*

---

## Example Walkthrough

> **Note:** This walkthrough shows the simplest repair route: implementation repair. The pipeline also supports test-suite repair (collection errors routed to `TesterAgent.repair_tests`) and test-grounding review (ungrounded expectations routed to `TesterAgent.review_and_repair_test_grounding`).

**Task:** `OrderStateMachine` — 2 iterations, 1 subtle failure, clean repair

All content below is verbatim from run `20260512_115150`. Nothing is paraphrased or constructed.

---

### Step 1 — Raw Requirement

```text
Create an OrderStateMachine class for an ecommerce demo. It should support
create_order(order_id: str) -> None, pay(order_id: str) -> None,
ship(order_id: str) -> None, cancel(order_id: str) -> None,
get_status(order_id: str) -> str, and list_orders_by_status(status: str) -> list[str].
New orders start as 'created'. pay moves an order from 'created' to 'paid'.
ship moves an order from 'paid' to 'shipped'. cancel is allowed only from
'created' or 'paid', and moves the order to 'cancelled'. A shipped order cannot
be cancelled. Calling pay on anything other than 'created' should raise ValueError.
Calling ship on anything other than 'paid' should raise ValueError. Creating the
same order_id twice should raise ValueError. Missing order_id should raise ValueError
for pay, ship, cancel, and get_status. list_orders_by_status should return matching
order IDs sorted alphabetically. Valid statuses are 'created', 'paid', 'shipped',
and 'cancelled'. Invalid status should raise ValueError.
```

---

### Step 2 — Generated TaskSpec

The Orchestrator Agent converts the requirement into a structured `TaskSpec`.

**Class:** `OrderStateMachine`

**Methods:**

```text
create_order(order_id: str) -> None
pay(order_id: str) -> None
ship(order_id: str) -> None
cancel(order_id: str) -> None
get_status(order_id: str) -> str
list_orders_by_status(status: str) -> list[str]
```

**Business Rules:**

| Rule | Condition |
|------|-----------|
| Order Creation | `creating the same order_id twice → raise ValueError` |
| State Transition: Pay | `order state is not 'created' → raise ValueError` |
| State Transition: Ship | `order state is not 'paid' → raise ValueError` |
| State Transition: Cancel | `order state is 'shipped' → raise ValueError` |
| Missing Order | `missing order_id in pay, ship, cancel, get_status → raise ValueError` |
| List Orders by Status | `invalid status → raise ValueError` |

---

### Step 3 — Generated Test Suite

The Tester Agent generates a fixed pytest suite from the TaskSpec. No implementation code exists yet.

```python
def test_cancel_order_successfully():
    system = OrderStateMachine()
    system.create_order('order_1')
    system.cancel('order_1')
    assert system.get_status('order_1') == 'cancelled'

def test_cancel_order_in_shipped_state_raises_value_error():
    system = OrderStateMachine()
    system.create_order('order_1')
    system.pay('order_1')
    system.ship('order_1')
    with pytest.raises(ValueError):
        system.cancel('order_1')

def test_list_orders_by_invalid_status_raises_value_error():
    system = OrderStateMachine()
    with pytest.raises(ValueError):
        system.list_orders_by_status('invalid_status')
```

11 tests total. Each test targets a specific business rule.

---

### Step 4 — Iteration 1: FAILED

The Developer Agent generates the initial implementation. The Pytest Runner executes the fixed suite.

**Result: 10 passed, 1 failed**

```text
FAILED test_generated.py::test_cancel_order_successfully

________________________ test_cancel_order_successfully ________________________

    def test_cancel_order_successfully():
        system = OrderStateMachine()
        system.create_order('order_1')
        system.cancel('order_1')
>       assert system.get_status('order_1') == 'cancelled'
E       AssertionError: assert 'canceled' == 'cancelled'
E
E         - cancelled
E         ?       -
E         + canceled

test_generated.py:58: AssertionError
========================= 1 failed, 10 passed in 0.02s =========================
```

**Failing line (`generated_code_iter1.py`):**

```python
self.orders[order_id] = 'canceled'   # American spelling — test expects 'cancelled'
```

---

### Step 5 — Failure Analysis

The Failure Analyzer reads the pytest output and produces a structured diagnosis (`failure_analysis_iter1.json`):

```json
{
  "primary_failure_type": "assertion_mismatch",
  "primary_blamed_artifact": "implementation",
  "recommended_action": "repair_implementation",
  "should_modify_code": true,
  "should_modify_tests": false,
  "should_review_spec": false,
  "routing_reason": "The implementation returns 'canceled' but the spec requires 'cancelled'. This is an implementation spelling error.",
  "failed_tests": [
    {
      "test_name": "test_cancel_order_successfully",
      "failure_type": "assertion_mismatch",
      "blamed_artifact": "implementation",
      "expected": "cancelled",
      "actual": "canceled",
      "confidence": 0.95,
      "error_message": "AssertionError: assert 'canceled' == 'cancelled'"
    }
  ]
}
```

The diagnosis identifies the exact cause before the Developer Agent is re-prompted.

---

### Step 6 — Iteration 2: PASSED

The Developer Agent receives the failure analysis and produces a corrected implementation.

**Fix (`generated_code_iter2.py`):**

```python
# 'canceled' → 'cancelled' in valid_states
self.valid_states = {'created', 'paid', 'shipped', 'cancelled'}

# 'canceled' → 'cancelled' in cancel()
self.orders[order_id] = 'cancelled'
```

**Result: 11 passed**

```text
========================= 11 passed in 0.01s =========================
```

---

### Step 7 — Quality Critic Verdict

The Code Quality Critic reviews the passing implementation for overfitting or rule violations.

**`quality_report_iter2.json`:**

```json
{
  "passed": true,
  "flags": [],
  "summary": "The code correctly implements the business rules without any signs of overfitting or anomalies."
}
```

Run complete. All artifacts written to `artifacts/runs/20260512_115150/`.

---

## Known Limitations

- No execution sandboxing (generated code runs in the local process environment)
- Single-candidate generation only (no parallel candidate sampling)
- The system does not yet detect repeated stuck failures across iterations
- The system does not yet roll back to the best previous implementation after a repair regression
- The Code Quality Critic can produce false positives, especially around numeric constants that are explicitly part of the spec
- Generated tests can still contain ungrounded expectations even after initial generation
- Test grounding review exists, but its own judge quality is not yet evaluated
- There is no independent hidden-test validation yet
- No dataset-level regression harness

---

## Next Engineering Milestones

1. **FailureProgressAnalyzer** — Detect repeated failure signatures, stuck loops, and repair regressions across iterations.
2. **Judge evaluation harness** — Evaluate FailureAnalyzer, Test Grounding Reviewer, and CodeQualityCritic on labeled examples.
3. **Test-suite validation stage** — Validate generated tests against the spec before implementation repair begins.
4. **Best-artifact rollback** — Roll back to the best previous implementation when repair makes the system worse.

**Longer-term:** sandboxed execution, parallel candidate generation, LangGraph orchestration runtime, dataset-level regression harness.

---

## Project Structure

```text
ai-software-delivery-pipeline/
├── pyproject.toml
├── README.md
├── .env.example
├── examples/
│   ├── run_shipping.py
│   ├── run_shopping_cart.py
│   └── generate_report.py
├── artifacts/
│   └── runs/
│       └── {run_id}/
│           ├── task_spec.json
│           ├── test_suite.py
│           ├── generated_code_iter1.py
│           ├── generated_code_iter2.py
│           ├── execution_result_iter1.json
│           ├── failure_analysis_iter1.json
│           ├── quality_report_iterN.json
│           ├── failure_trace_context.json
│           ├── summary.json
│           └── run_report.md
├── src/
│   └── ai_delivery/
│       ├── models/
│       │   ├── task_spec.py
│       │   ├── generated_artifact.py
│       │   ├── execution_result.py
│       │   ├── failure_analysis.py
│       │   └── quality_report.py
│       ├── agents/
│       │   ├── orchestrator.py
│       │   ├── tester.py
│       │   ├── developer.py
│       │   ├── failure_analyzer.py
│       │   └── critic.py
│       ├── prompts/
│       │   ├── task_context.py
│       │   ├── orchestrator_prompts.py
│       │   ├── tester_prompts.py
│       │   ├── developer_prompts.py
│       │   ├── failure_analyzer_prompts.py
│       │   └── critic_prompts.py
│       ├── execution/
│       │   └── pytest_runner.py
│       ├── reporting/
│       │   ├── __init__.py
│       │   └── report_generator.py
│       └── pipeline/
│           └── run_once.py
└── tests/
```

---

## Installation

```bash
pip install -e .
```

---

## Configuration

Copy `.env.example` to `.env` and configure your environment variables:

```bash
cp .env.example .env
```

---

## Usage

### Example 1 — module-level function

`run_shipping.py` generates a `calculate_shipping` function from a detailed natural-language spec:

```bash
python3 examples/run_shipping.py
```

The orchestrator sets `class_name=""` and puts the function signature in `methods`. The tester imports and calls the function directly.

### Example 2 — class artifact

`run_shopping_cart.py` generates a `ShoppingCart` class from a loose natural-language requirement:

```bash
python3 examples/run_shopping_cart.py
```

The orchestrator sets `class_name="ShoppingCart"` and populates `methods` with the public API. The tester instantiates the class and tests behavior through its methods.

### Example 3 — batch benchmark

`run_batch.py` runs the MVP Benchmark Suite A (5 progressive tasks):

```bash
python3 examples/run_batch.py
```

This executes the pipeline for all benchmark tasks and produces a summary table with pass/fail status and iteration counts.

### Report generation

Generate or regenerate a report for the latest run:

```bash
python3 examples/generate_report.py
```

Generate a report for a specific historical run:

```bash
python3 examples/generate_report.py 20260512_004408
```

---

## Core Artifacts

Each run produces explicit artifacts under:

```text
artifacts/runs/{run_id}/
```

### `task_spec.json`

The structured interpretation of the user requirement.

For a class artifact:

```json
{
  "class_name": "ShoppingCart",
  "methods": [
    "add_item(item_name: str, price: float, quantity: int = 1) -> None",
    "remove_item(item_name: str, quantity: int | None = None) -> None",
    "subtotal() -> float",
    "apply_coupon(discount_amount: float) -> None",
    "total() -> float"
  ],
  "business_rules": [
    { "name": "Negative price", "rule": "price < 0.0 → raise ValueError" },
    { "name": "Item merging", "rule": "item_name in cart → increase quantity" },
    { "name": "Total floor", "rule": "total < 0.0 → return 0.0" }
  ]
}
```

For a module-level function artifact, `class_name` is `""` and `methods` contains the function signature:

```json
{
  "class_name": "",
  "methods": ["calculate_shipping(cart_total: float, package_weight: float, destination_zone: str) -> float"],
  "business_rules": [
    { "name": "Free shipping", "rule": "cart_total > 150.0 → return 0.0" },
    { "name": "Weight tier 1", "rule": "package_weight <= 2.0 → base cost 5.0" },
    { "name": "Regional surcharge", "rule": "destination_zone == 'regional' → add 4.0" }
  ]
}
```

### `test_suite.py`

A fixed pytest suite generated from the task spec.

The tests should represent executable behavior, including:

- normal cases
- boundary cases
- validation rules
- invalid inputs
- domain-specific constraints

### `generated_code_iterN.py`

The implementation generated or refined by the Developer Agent for each iteration.

### `execution_result_iterN.json`

The raw pytest execution result for each iteration.

### `failure_analysis_iterN.json`

A structured diagnosis generated from failed pytest output.

Includes:

- per-test `failure_type` (normalized enum: `assertion_mismatch`, `spec_test_conflict`, `test_syntax_error`, etc.)
- `blamed_artifact` — which artifact is responsible: `implementation`, `test_suite`, or `spec_or_test_expectation`
- `recommended_action` — next repair route: `repair_implementation`, `repair_test_suite`, `review_test_grounding`, etc.
- `should_modify_code` / `should_modify_tests` / `should_review_spec` — routing flags
- `routing_reason` — one-sentence explanation of the routing decision
- `failure_signature` — stable normalized signature used to detect repeated failures
- `lesson` — reusable insight for future iterations

### `quality_report_iterN.json`

The Code Quality Critic’s review after tests pass.

This checks whether the code appears to:

- implement the business rules generally
- avoid hardcoded test-case patches
- avoid misleading logic
- avoid overfitting to the visible tests

### `run_report.md`

A human-readable report generated from the run artifacts.

---

## Components

### Orchestrator Agent

Converts the raw user request into a structured `TaskSpec`.

The task spec describes the artifact's public API:

- `class_name` — the class name, or `""` for a module-level function task
- `methods` — list of public callable signatures without `def`; method signatures for classes, function signatures for function tasks
- `module_name` — the Python module to generate
- `description` — one-sentence description
- `success_criteria` — measurable acceptance criteria
- `edge_cases` — edge cases to handle
- `business_rules` — named rules with precise conditions

The Orchestrator is responsible for turning vague user language into a clear behavioral contract.

---

### Tester Agent

Creates a pytest suite from the structured `TaskSpec`.

The initial test suite is generated once and is fixed during all implementation repair iterations. The Tester Agent is called again only when the failure analyzer attributes the problem to the test artifact itself:

- `repair_tests` — fixes structural issues: syntax errors, indentation errors, import failures. Does not change business intent.
- `review_and_repair_test_grounding` — reviews test *expected values* against the spec's declared return types and method contracts. Changes a test only if its expectation is not supported by the spec.

Good tests should be rule-specific. For a function task:

```python
def test_cart_total_over_150_returns_free_shipping():
    assert calculate_shipping(151.0, 5.0, "local") == 0.0
```

For a class task:

```python
def test_negative_price_raises_value_error():
    cart = ShoppingCart()
    with pytest.raises(ValueError):
        cart.add_item("apple", -1.0)
```

Each failing test points to a specific violated rule, making failure analysis easier.

---

### Developer Agent

Generates the initial implementation and later refines it.

The Developer receives:

- task specification
- fixed test suite
- previous code version
- pytest failure output
- failure analysis
- prior failure history

During refinement, only the Developer Agent is called again. The Tester Agent is not rerun unless the task spec changes.

---

### Pytest Runner

Executes the generated test suite against the generated implementation.

It captures:

- pass/fail status
- exit code
- stdout
- stderr
- failed test names
- assertion errors
- stack traces

This is the factual feedback source for the loop.

---

### Failure Analyzer

Converts raw pytest failure output into a structured `FailureAnalysis` artifact with normalized routing fields.

Example:

```json
{
  "primary_failure_type": "spec_test_conflict",
  "primary_blamed_artifact": "spec_or_test_expectation",
  "recommended_action": "review_test_grounding",
  "should_modify_code": false,
  "should_modify_tests": true,
  "should_review_spec": true,
  "routing_reason": "The test expected room name in get_bookings output, but the TaskSpec declares get_bookings(room: str) -> list[tuple[int, int]].",
  "failed_tests": [
    {
      "test_name": "test_get_bookings_returns_correct_slots",
      "failure_type": "spec_test_conflict",
      "blamed_artifact": "spec_or_test_expectation",
      "expected": "[('room1', 9, 11)]",
      "actual": "[(9, 11)]",
      "confidence": 0.92
    }
  ]
}
```

The failure type and routing flags drive which agent is called next. The system does not always send failures back to the Developer Agent.

---

### Code Quality Critic

Runs after tests pass.

Its purpose is to catch cases where the implementation passes tests but is still suspicious.

Examples of problems the critic should flag:

- hardcoded test-case values
- negative surcharges unless specified
- comments like “adjusted to satisfy test”
- exact-value hacks
- misleading unused structures
- logic that contradicts the business rules

Passing tests are necessary, but not always enough. The critic acts as an additional quality gate.

---

### Run Report Generator

Generates `run_report.md` from run artifacts.

The report includes:

- summary
- task spec
- business rules table
- test suite list
- iteration timeline
- failure analysis
- critic verdicts
- final implementation
- quality sign-off

This turns every run into an auditable engineering artifact.

---

## Test-Driven Code Generation Loop

The loop has six main stages.

---

### Stage 1: Task Specification

The workflow begins with a raw user requirement.

Example:

```text
Hey, I need a Python function for our checkout service.
The function should be called calculate_shipping and take cart_total,
package_weight, and destination_zone.
```

The Orchestrator Agent converts this into a structured `TaskSpec`.

At this point, no code exists yet.

---

### Stage 2: Test Synthesis

The Tester Agent receives the `TaskSpec` and generates a fixed pytest suite.

The tests are based on the specification, not on generated code.

This matters because tests should represent expected behavior, not merely adapt to an implementation.

The output is:

```text
test_suite.py
```

---

### Stage 3: Code Synthesis

The Developer Agent receives the same `TaskSpec` and generates the initial Python implementation.

The output is:

```text
generated_code_iter1.py
```

This first implementation is not trusted yet. It must be executed and validated.

---

### Stage 4: Execution and Validation

The Pytest Runner executes the fixed test suite against the generated implementation.

It records the result as:

```text
execution_result_iter1.json
```

If all tests pass, the pipeline moves to quality review.

If tests fail, the pipeline moves to failure analysis.

---

### Stage 5: Failure Analysis and Repair Routing

When tests fail, the Failure Analyzer reads the pytest output and produces a structured `FailureAnalysis` with normalized failure types, blamed artifact, and routing flags.

The Repair Router then selects the appropriate repair path:

**Route 1 — Implementation repair** (`should_modify_code = true`)

The Developer Agent receives TaskSpec, current code, pytest output, failure analysis, and failure history. It produces a revised implementation.

**Route 2 — Test suite repair** (`should_modify_tests = true`, `should_modify_code = false`)

The Tester Agent's `repair_tests` method fixes structural issues: syntax errors, indentation errors, import failures. Business intent is preserved.

**Route 3 — Test grounding review** (`should_review_spec = true`, `should_modify_tests = true`)

The Tester Agent's `review_and_repair_test_grounding` method checks whether failing test expectations are consistent with the spec's declared return types. A test is only changed if its expectation is not supported by the spec.

The same fixed test suite (or repaired suite) is executed again after each repair. This loop continues until tests pass, the system reaches max iterations, or no valid repair route is found.

---

### Stage 6: Quality Review and Report Generation

When tests pass, the Code Quality Critic reviews the final code.

If the critic approves the implementation, the run succeeds.

If the critic rejects it, the system can send the critic feedback back to the Developer Agent for another refinement round.

Finally, the Run Report Generator writes:

```text
run_report.md
```

---

## Current Status

This is a working MVP of an evaluation-driven AI software delivery loop for small Python function/class tasks.

The project is intentionally scoped: the goal is not broad code generation, but measurable repair behavior under executable feedback.

Current capabilities:

- raw user requirement input
- structured task specification with public API (`class_name` + `methods`)
- class artifacts and module-level function artifacts
- named business rules
- test generation grounded on the public API
- code generation
- pytest execution
- failure analysis
- iterative refinement
- quality criticism with class-specific checks
- run report with Task Spec section (type, class, methods table)
- two working examples: `run_shipping.py` and `run_shopping_cart.py`

---

## License

MIT
