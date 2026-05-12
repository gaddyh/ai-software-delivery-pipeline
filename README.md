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

Run the shipping pipeline:

```bash
python3 examples/run_shipping.py
```

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

Example business-rule format:

```json
"business_rules": [
  {
    "name": "Free shipping",
    "rule": "cart_total > 150.0 → return 0.0"
  },
  {
    "name": "Weight tier 1",
    "rule": "package_weight <= 2.0 → base cost 5.0"
  },
  {
    "name": "Regional surcharge",
    "rule": "destination_zone == 'regional' → add 4.0"
  }
]
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

The task spec includes:

- raw requirement
- function name
- function signature
- module name
- description
- success criteria
- edge cases
- named business rules

The Orchestrator is responsible for turning vague user language into a clear behavioral contract.

---

### Tester Agent

Creates a fixed pytest suite from the structured `TaskSpec`.

The Tester Agent runs once per task.

It should not depend on generated implementation code. Its job is to encode expected behavior from the task specification.

Good tests should be rule-specific:

```python
def test_cart_total_over_150_returns_free_shipping():
    assert calculate_shipping(151.0, 5.0, "local") == 0.0
```

This makes failure analysis easier because each failing test points to a specific violated rule.

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
- structured task specification
- named business rules
- test generation
- code generation
- pytest execution
- failure analysis
- iterative refinement
- quality criticism
- run report generation

Next recommended step:

> Add a small benchmark runner that executes 5–10 task prompts and produces aggregate metrics such as success rate, average iterations, and critic-fail count.

---

## License

MIT
