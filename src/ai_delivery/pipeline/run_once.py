"""Single-run pipeline for shipping software."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.failure_trace import FailureTrace, IterationRecord
from ai_delivery.agents.orchestrator import OrchestratorAgent
from ai_delivery.agents.developer import DeveloperAgent
from ai_delivery.agents.tester import TesterAgent

MAX_ITERATIONS = 3


def _extract_traceback(output: str) -> str:
    """Extract the first error block from pytest stdout."""
    lines = output.splitlines()
    capture = False
    block: list[str] = []
    for line in lines:
        if line.startswith("FAILED") or "Error" in line or "assert" in line.lower():
            capture = True
        if capture:
            block.append(line)
            if len(block) >= 10:
                break
    return "\n".join(block)


class RunOncePipeline:
    """Pipeline that runs the six-stage TDG loop once per task."""

    def __init__(self, artifacts_dir: str = "artifacts/runs"):
        """Initialize the pipeline."""
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.orchestrator = OrchestratorAgent()
        self.developer = DeveloperAgent()
        self.tester = TesterAgent()

    def run(self, task_spec: TaskSpec) -> dict:
        """Execute the six-stage TDG loop for the given task."""
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "run_id": run_id,
            "task_spec": task_spec,
            "code_artifact": None,
            "test_artifact": None,
            "execution_result": None,
            "success": False,
            "iterations": 0,
        }

        failure_trace: Optional[FailureTrace] = None
        execution_result = None
        iteration = 0

        try:
            # ── Stage 1: Task assignment ──────────────────────────────────
            print(f"\nStage 1 \u2502 Task assigned: {task_spec.description}")

            # ── Stage 2: Initial code synthesis ──────────────────────────
            print("Stage 2 \u2502 Generating initial code...")
            code_artifact = self.developer.generate_code(task_spec, failure_trace=None)
            code_file = run_dir / "generated_code_iter1.py"
            code_file.write_text(code_artifact.content)
            print(f"         \u2514 saved: {code_file.name}")

            # ── Stage 3: Test synthesis (ONCE — fixed for all iterations) ─
            print("Stage 3 \u2502 Generating test suite (fixed for all iterations)...")
            test_artifact = self.tester.generate_tests(task_spec, code_artifact.content)
            test_file = run_dir / "test_suite.py"
            test_file.write_text(test_artifact.content)
            print(f"         \u2514 saved: {test_file.name}")
            results["test_artifact"] = test_artifact

            # ── Stages 4-5: Execute → evaluate → refine loop ─────────────
            print(f"Stages 4-5 \u2502 Refinement loop (max {MAX_ITERATIONS} iterations)...")

            for iteration in range(1, MAX_ITERATIONS + 1):
                current_code_file = run_dir / f"generated_code_iter{iteration}.py"

                print(f"\n  [Iteration {iteration}/{MAX_ITERATIONS}] Running test suite against {current_code_file.name}...")

                # Stage 4: execute the fixed test suite against current code
                execution_result = self.tester.execute_tests(
                    test_artifact, str(current_code_file)
                )
                result_file = run_dir / f"execution_result_iter{iteration}.json"
                result_file.write_text(execution_result.model_dump_json(indent=2))

                if execution_result.status.value == "success":
                    print(f"  \u2713 PASSED \u2014 all tests green")
                    break

                # Stage 5: parse failures, build FailureTrace, refine code
                failed_tests = self.tester.parse_failures(execution_result)
                feedback = self.tester.review_results(execution_result)
                first_line = feedback.splitlines()[0][:120] if feedback else ""
                print(f"  \u2717 FAILED \u2014 {first_line}")
                print(f"         Failed tests: {', '.join(failed_tests) if failed_tests else 'see output'}")

                record = IterationRecord(
                    iteration=iteration,
                    failed_tests=failed_tests,
                    traceback_summary=_extract_traceback(execution_result.output),
                    exit_code=execution_result.exit_code,
                )
                if failure_trace is None:
                    failure_trace = FailureTrace(history=[record])
                else:
                    failure_trace.history.append(record)

                if iteration < MAX_ITERATIONS:
                    print(f"  \u2192 Sending FailureTrace (iteration {iteration} history) to Developer Agent...")
                    code_artifact = self.developer.generate_code(task_spec, failure_trace)
                    next_code_file = run_dir / f"generated_code_iter{iteration + 1}.py"
                    next_code_file.write_text(code_artifact.content)
                    print(f"  \u2192 Refined code saved: {next_code_file.name}")

            results["code_artifact"] = code_artifact
            results["execution_result"] = execution_result
            results["iterations"] = iteration

            # ── Stage 6: Success / advancement ───────────────────────────
            success = self.orchestrator.validate_result(code_artifact, execution_result)
            results["success"] = success

            trace_file = run_dir / "failure_trace_context.json"
            trace_data = failure_trace.model_dump() if failure_trace else {"history": []}
            trace_file.write_text(json.dumps(trace_data, indent=2))

            print(f"\nStage 6 \u2502 {'SUCCESS' if success else 'FAILURE'} after {iteration} iteration(s)")
            print(f"         \u2514 failure_trace_context.json: {len(trace_data['history'])} failure record(s)")

        except Exception as e:
            print(f"Pipeline error: {e}")
            results["error"] = str(e)

        summary_file = run_dir / "summary.json"
        summary = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "task_description": task_spec.description,
            "success": results.get("success", False),
            "iterations": results.get("iterations", 0),
            "execution_status": results["execution_result"].status.value
            if results.get("execution_result") else None,
        }
        summary_file.write_text(json.dumps(summary, indent=2))
        return results

    def get_run_history(self) -> list[dict]:
        """Get history of all pipeline runs."""
        history = []
        for run_dir in sorted(self.artifacts_dir.iterdir()):
            if run_dir.is_dir():
                summary_file = run_dir / "summary.json"
                if summary_file.exists():
                    with open(summary_file) as f:
                        history.append(json.load(f))
        return history
