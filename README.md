# AI Software Delivery Pipeline

An AI-powered software delivery pipeline that uses autonomous agents to develop, test, and ship software automatically.

## Project Structure

```
ai-software-delivery-pipeline/
├── pyproject.toml
├── README.md
├── .env.example
├── examples/
│   └── run_shipping_once.py
├── artifacts/
│   └── runs/
├── src/
│   └── ai_delivery/
│       ├── models/
│       │   ├── task_spec.py
│       │   ├── generated_artifact.py
│       │   └── execution_result.py
│       ├── agents/
│       │   ├── orchestrator.py
│       │   ├── tester.py
│       │   └── developer.py
│       ├── execution/
│       │   └── pytest_runner.py
│       └── pipeline/
│           └── run_once.py
└── tests/
```

## Installation

```bash
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure your environment variables:

```bash
cp .env.example .env
```

## Usage

Run the shipping pipeline once:

```bash
python examples/run_shipping_once.py
```

## Components

- **Orchestrator Agent**: Coordinates the overall pipeline execution
- **Developer Agent**: Generates code based on task specifications
- **Tester Agent**: Writes and executes tests to validate generated code
- **Pytest Runner**: Executes pytest and captures results

---

## Test-Driven Code Generation Loop

The following six stages describe the full execution of the loop, from the initial task assignment through code synthesis, test generation, validation, iterative refinement, and final success.

Each stage represents a discrete handoff between agents. The output of one stage becomes the input to the next.

### Stage 1: Task Assignment

The workflow begins when the Orchestrator Agent assigns a concrete task to the Developer Agent.

**Example task:**

```
Write a function calculate_shipping(cart_total, weight)
that returns the shipping cost after applying appropriate discounts.
```

At this point, no code exists yet. The task enters the generation pipeline.

### Stage 2: Code Synthesis

The Developer Agent generates an initial Python implementation.

It uses the available repository context to:

- follow existing code style conventions
- choose appropriate libraries
- structure the function according to project patterns
- produce an initial solution

The generated code is saved as an artifact in the shared workflow state. Specifically, the code is written to a sandboxed file system inside a Docker container, where it can be executed and tested in isolation.

The file path and code content are also stored in the `AgentState` dictionary, making them available to downstream agents without requiring direct file-system access.

This first implementation is the developer agent's best attempt based on the requirement. But it is not trusted yet — it still needs verification.

### Stage 3: Test Synthesis

The generated code and the original task specification are passed to the Tester Agent.

The tester agent receives a clear directive:

```
Write a comprehensive pytest test suite that verifies the code against the requirements,
including important edge cases.
```

The tester agent generates tests that check the expected behavior of the implementation. One important example is a test for negative weight — even though this edge case may not have been explicitly mentioned in the original requirement, the tester identifies it as essential for robust behavior.

> **Stages 2 and 3 execute in sequence, not in parallel.** The tester agent needs the developer agent's code as input in order to generate meaningful tests.

The outputs of these two stages are:

```
Implementation code
+
Test suite
```

Both artifacts then flow into the execution environment.

### Stage 4: Execution and Validation

The implementation code and test suite are saved into a sandboxed environment (Docker). The system then runs the test suite using `pytest`.

The test runner captures:

- which tests passed
- which tests failed
- assertion errors
- stack traces
- relevant execution output

This concrete failure output becomes critical feedback for the next iteration. Unlike vague LLM self-reflection, test output is factual and grounded.

### Stage 5: The Refinement Loop

The workflow reaches a decision point: **did all tests pass?**

If the answer is no, the system follows the failure path. The stack trace is parsed programmatically using Python's built-in `traceback` module. This extracts structured information such as:

- file name
- line number
- function name
- error message

This structured failure information is injected into the refinement prompt. The developer agent does not merely receive a message saying *"the tests failed"* — instead, it receives the full context:

```
Original task specification
+
Current code version
+
Complete pytest output
+
Stack traces
+
Assertion errors
+
Summary of prior failed attempts
```

This allows the agent to focus on the exact remaining problem instead of guessing. The updated code is then saved back into the sandbox, the tests are executed again, and the results are evaluated. This loop continues until the tests pass or the system reaches a stopping condition.

### Stage 6: Success and Advancement

When all tests pass, the workflow advances to the next stage. The validated code can now move forward to:

- integration
- documentation
- deployment
- additional review
- downstream workflows

The **Failure Trace Context** captures the full history of the refinement loop:

- how many iterations were required
- which tests failed at each attempt
- what errors were encountered
- how the code changed in response to feedback

This trace is useful for three reasons:

1. It provides transparency into the agent workflow.
2. It supports debugging when convergence fails.
3. It creates valuable training and evaluation data for future improvement.

Over time, these failure-resolution pairs can be analyzed and reused to improve the system's first-attempt success rate.

---

## Why This Architecture Matters

This iterative loop is the core pattern behind reliable code agents:

```
Generate → Test → Fail → Refine → Test Again → Pass
```

It matters because it uses factual feedback from real tools to correct probabilistic LLM output. Without this loop, the agent simply generates code once and hopes it works. With this loop, the agent becomes a self-correcting system that demonstrates correctness through evidence.

The architecture also shows that agents do not operate in isolation. They interact with real development infrastructure:

- file systems
- Docker containers
- test runners
- compilers
- execution logs
- observability platforms

The agent is not just chatting about code — it is writing files, running tests, parsing failures, and improving based on executable feedback.

---

## License

MIT
