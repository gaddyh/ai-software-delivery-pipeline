# AI Software Delivery Pipeline

An evaluation-driven AI software delivery pipeline that turns a natural-language requirement into tested, refined, and quality-reviewed Python code.

The system is not a chatbot demo. It is an artifact-based software generation loop:

```text
User Requirement
→ Structured Task Spec
→ Fixed Test Suite
→ Initial Code
→ Pytest Execution
→ Failure Analysis
→ Code Refinement
→ Quality Critic
→ Run Report
```

The core idea is simple:

> Tests become executable behavioral specifications, and real tool output drives refinement.

---

## Project Goal

This project explores a practical pattern for reliable code-generation agents.

Instead of asking an LLM to generate code once and hoping it works, the system:

1. Interprets a user requirement.
2. Converts it into a structured task specification.
3. Generates a fixed pytest test suite from that spec.
4. Generates implementation code.
5. Runs the tests.
6. Sends failure traces and failure analysis back to the developer agent.
7. Refines the code until tests pass.
8. Runs a quality critic to detect overfitting or suspicious implementation logic.
9. Writes a full run report.

---

## Current Pipeline Flow

```text
1. User Message
   ↓
2. Orchestrator Agent
   Produces structured TaskSpec
   ↓
3. Tester Agent
   Produces a fixed pytest suite from the TaskSpec
   ↓
4. Developer Agent
   Produces initial implementation
   ↓
5. Pytest Runner
   Executes tests in an isolated environment
   ↓
6. Failure Analyzer
   Converts pytest output into likely bug + patch instruction
   ↓
7. Developer Agent
   Refines code using failure trace + failure analysis
   ↓
8. Repeat execution/refinement until tests pass or max iterations reached
   ↓
9. Code Quality Critic
   Reviews passing code for overfitting or rule violations
   ↓
10. Run Report Generator
    Writes run_report.md
```

Important rule:

```text
Code failed → return to Developer Agent
Spec changed → regenerate tests with Tester Agent
```

The Tester Agent runs once per task. During refinement, the same fixed test suite is reused.

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

`run_batch.py` runs the MVP 1 benchmark set (5 progressive tasks of increasing difficulty):

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

## Why This Architecture Matters

This project demonstrates the core pattern behind reliable code-generation agents:

```text
Spec → Tests → Code → Execute → Analyze → Refine → Critique → Report
```

The system uses real tool output instead of vague self-reflection.

The important difference is this:

```text
LLM output is probabilistic.
Test results are factual.
```

By grounding the agent in executable feedback, the system can systematically improve instead of merely generating code once and hoping it works.

---

## What This Project Shows

This project demonstrates practical AI engineering skills:

- structured output modeling with Pydantic
- agent role separation
- pytest as an executable evaluator
- iterative refinement loops
- failure trace capture
- failure analysis
- quality criticism after green tests
- artifact-based development
- run-level observability
- report generation
- evaluation-driven software generation

---

## Current Status

Project 1 MVP is working.

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

## MVP 1 Benchmark Results

Batch run executed on 2026-05-12 using the MVP 1 benchmark set (5 progressive tasks):

| # | Task | Status | Iterations |
|---|------|--------|------------|
| 1 | apply_discount (function) | ✓ Passed | 2 |
| 2 | calculate_ticket_price (function) | ✓ Passed | 1 |
| 3 | BankAccount (class) | ✓ Passed | 1 |
| 4 | Inventory (class) | ✓ Passed | 1 |
| 5 | GradeBook (class) | ✓ Passed | 1 |

**Summary:** 5/5 tasks passed (100% success rate)

**Metrics:**
- Average iterations to success: 1.2
- 4/5 tasks converged on first attempt
- 1 task (apply_discount) required 2 iterations due to floating-point precision edge case
- Quality critic approved all implementations
- No overfitting or suspicious patterns detected

**Note:** The benchmark demonstrates the system's ability to converge or produce useful failure reports, which is the MVP 1 standard.

---

## License

MIT
