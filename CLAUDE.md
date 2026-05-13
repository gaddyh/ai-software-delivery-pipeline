# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, from repo root)
pip install -e .
pip install -e ".[dev]"   # includes black, ruff, mypy

# Lint / format
ruff check src/
black src/

# Type checking
mypy src/

# Run unit tests (tests/ dir — currently empty; pipeline tests run via examples)
pytest

# Run a single example pipeline task
python examples/run_shipping.py
python examples/run_shopping_cart.py
python examples/run_ticket_task.py

# Run the benchmark suite (requires OPENAI_API_KEY)
python examples/run_batch.py                  # Suite A (base)
python examples/run_batch.py --benchmark hard # Suite B (hard)

# Generate / regenerate a run report
python examples/generate_report.py                   # latest run
python examples/generate_report.py <run_id>          # specific run

# Environment
cp .env.example .env   # then set OPENAI_API_KEY
```

## Architecture

The system is an evaluation-driven loop that converts a natural language requirement into a tested, critiqued Python artifact.

### Six-stage pipeline (`src/ai_delivery/pipeline/run.py`)

```
Stage 1 — Orchestrator  : user message → TaskSpec (structured behavioral contract)
Stage 2 — Developer     : TaskSpec → initial generated_code_iter1.py
Stage 3 — Tester        : TaskSpec + code → test_suite.py (FIXED for all iterations)
Stages 4–5 loop:
    Stage 4 — PytestRunner  : test_suite.py × generated_code_iterN.py → ExecutionResult
    Stage 5a — FailureAnalyzer : ExecutionResult → FailureAnalysis (if failed)
    Stage 5b — Developer    : FailureAnalysis + FailureTrace → generated_code_iterN+1.py
    Stage 5c — Critic       : (if passed) → QualityReport; re-enter loop if rejected
Stage 6 — ReportGenerator : all artifacts → run_report.md
```

The test suite is generated **once** and never regenerated during repair. Only the Developer Agent is called on each repair iteration.

### Key design invariant

Tests are authored from the `TaskSpec`, not from generated code. This enforces that the spec — not the implementation — is the source of truth.

### LLM abstraction (`src/ai_delivery/llm/`)

`LLMClient` is an abstract base with two implementations:
- `OpenAIClient` — uses `gpt-4o` by default with OpenAI structured output (`json_schema` strict mode or `json_object` mode)
- `MockLLMClient` — deterministic stub for development without an API key

All agents accept an optional `llm: LLMClient` parameter. When `llm=None` (no `OPENAI_API_KEY`), every agent falls back to a stub/regex path so the pipeline runs end-to-end without API calls.

### Models (`src/ai_delivery/models/`)

All structured data is Pydantic v2:
- `TaskSpec` — behavioral contract; `class_name=""` signals a module-level function task; `is_class_task` property distinguishes class vs. function artifacts
- `FailureAnalysis` / `StructuredTestFailure` — per-test structured facts extracted from pytest output (not inferred from test names)
- `FailureTrace` / `IterationRecord` — rolling history of all failures across iterations, fed back to the Developer Agent
- `QualityReport` — critic verdict; `passed=False` sends code back for rewrite even after tests pass

### Agents (`src/ai_delivery/agents/`)

Each agent has a corresponding prompt module under `src/ai_delivery/prompts/`. Prompts are plain functions returning strings; the `FAILURE_ANALYSIS_SCHEMA` in `failure_analyzer_prompts.py` is the JSON Schema used with OpenAI's strict structured output mode.

### Artifacts

Every run writes to `artifacts/runs/{run_id}/`:
- `task_spec.json`, `test_suite.py`
- `generated_code_iterN.py`, `execution_result_iterN.json`
- `failure_analysis_iterN.json` (only on failed iterations)
- `quality_report_iterN.json` (only on passed iterations)
- `failure_trace_context.json`, `summary.json`, `run_report.md`

`artifacts/` is gitignored except for `.DS_Store`.

### Benchmark task definitions

`benchmark_user_messages.py` (repo root) contains `mvp1_benchmark_set` (Suite A, 5 tasks) and `harder_mvp1_benchmark_set` (Suite B, 5 harder tasks). These are the canonical evaluation inputs.
