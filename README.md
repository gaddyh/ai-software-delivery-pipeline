# AI Software Delivery Pipeline

Evaluation-driven system for reliable Python code generation and repair.

The system converts a natural language software requirement into executable artifacts:

```text
Requirement
→ Structured Spec
→ Pytest Suite
→ Generated Code
→ Real Execution
→ Failure Analysis
→ Iterative Repair
→ Quality Critique
→ Engineering Report
```

The system uses executable pytest feedback, structured failure analysis, and iterative repair loops to improve generated code reliability over multiple iterations.

Unlike one-shot code generation demos, this project uses executable validation loops grounded in real pytest output.

---

[Benchmark](#benchmark-results) · [Architecture](#architecture) · [Walkthrough](#example-walkthrough) · [What This Proves](#what-this-project-proves) · [Known Limitations](#known-limitations) · [Future Work](#planned-improvements)

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

### MVP Benchmark Suite B

Batch run using 5 tasks with increased complexity, recorded before the failure-analysis and repair-mode improvements:

| # | Task | Status | Iterations |
|---|------|--------|------------|
| 1 | calculate_coupon_discount | ✗ Failed | 6 |
| 2 | calculate_late_fee | ✓ Passed | 2 |
| 3 | LoginAttemptTracker | ✓ Passed | 1 |
| 4 | OrderStateMachine | ✓ Passed | 1 |
| 5 | RoomBooking | ✓ Passed | 2 |

**80% task convergence (4/5)** — pre-repair-mode upgrade

**Known weakness at the time:** Arithmetic composition with caps/modifiers (tiered calculations, override rules, caps). The failure analyzer was inferring failure category from test names rather than reading assertion evidence, and the developer was allowed to drift into business-rule changes on precision failures.

**Status:** This result predates the Phase 1 repair-mode upgrade (failure category extraction, `_get_repair_mode()`, PRECISION/FORCED_PRECISION repair modes). Suite B should be rerun against the updated codebase before treating this as a current result.

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
Tester Agent → Fixed Pytest Suite
      ↓
Developer Agent → Initial Code
      ↓
Pytest Runner
  ↓ (fail)               ↓ (pass)
Failure Analyzer    Quality Critic → Run Report
      ↓                   ↑
Developer Agent (repair) ─┘
```

The Tester Agent runs once per task. The test suite remains fixed during all repair iterations.

```text
Code failed → return to Developer Agent
Spec changed → regenerate tests with Tester Agent
```

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
  "failed_tests": ["test_cancel_order_successfully"],
  "inferred_rules": [
    "An order should transition to 'cancelled' state (with British spelling) when canceled successfully."
  ],
  "likely_bug": "The system returns 'canceled' instead of 'cancelled', indicating a spelling inconsistency.",
  "patch_instruction": "Review the OrderStateMachine to ensure it uses 'cancelled' (with British English spelling) instead of 'canceled' for order cancellation state consistency, and update the get_status method accordingly.",
  "expected_value": "cancelled",
  "actual_value": "canceled",
  "difference": "Difference in spelling: 'canceled' in American English vs 'cancelled' in British English.",
  "failure_category": "validation_error",
  "confidence": 0.9
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
- No retrieval grounding for spec generation
- No dataset-level regression harness
- Limited benchmark diversity (Python functions and classes only)
- No semantic equivalence verification between iterations

---

## Planned Improvements

- Sandboxed execution environment
- Parallel candidate generation with selection
- Self-play benchmark generation
- MLflow/Evidently evaluation tracking
- Dataset-driven regression testing
- LangGraph orchestration runtime
- Multi-language support
- Retrieval-augmented spec grounding

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

- failed tests
- inferred rules
- likely bug
- patch instruction

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

Creates a fixed pytest suite from the structured `TaskSpec`.

The Tester Agent runs once per task.

It should not depend on generated implementation code. Its job is to encode expected behavior from the task specification.

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

Converts raw pytest failure output into a structured debugging artifact.

Example:

```json
{
  "failed_tests": [
    "test_weight_tier_2_base_cost",
    "test_regional_destination_surcharge"
  ],
  "inferred_rules": [
    "For package_weight 3.0 in local zone, shipping should be 10.0.",
    "For package_weight 3.0 in regional zone, shipping should be 14.0."
  ],
  "likely_bug": "The implementation incorrectly calculates base costs and surcharges.",
  "patch_instruction": "Correct the weight tiers and apply destination surcharge after base cost calculation."
}
```

The Failure Analyzer reduces ambiguity before sending the problem back to the Developer Agent.

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

### Stage 5: Failure Analysis and Refinement

When tests fail, the Failure Analyzer reads the pytest output and produces a structured diagnosis.

The Developer Agent then receives:

```text
TaskSpec
+
Current code
+
Pytest output
+
Failure analysis
+
Failure history
```

The Developer produces a revised implementation:

```text
generated_code_iter2.py
```

The same fixed test suite is executed again.

This loop continues until:

- tests pass
- max iterations are reached
- the system fails to converge

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

Project 1 MVP is working for small Python function/class tasks.

The current version supports:

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
