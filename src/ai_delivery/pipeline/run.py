"""Single-run pipeline for shipping software."""

import json
import os
import re
import traceback
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
from ai_delivery.agents.failure_analyzer import FailureAnalyzerAgent
from ai_delivery.agents.critic import CodeQualityCriticAgent
from ai_delivery.llm.openai_client import OpenAIClient
from ai_delivery.reporting.report_generator import ReportGenerator

MAX_ITERATIONS = 6


def _extract_traceback(output: str) -> str:
    """Extract structured error info from pytest stdout.

    Mirrors the structured fields produced by Python's traceback module:
    file name, line number, function name, and error message.
    """
    # "  <file>.py:<lineno>: <context>" — pytest failure location lines
    location_re = re.compile(r"^\s{0,4}(\S+\.py):(\d+):\s+(.+)$", re.MULTILINE)
    # Pytest error lines prefixed with "E "
    error_re = re.compile(r"^E\s{1,3}(.+)$", re.MULTILINE)

    locations = location_re.findall(output)
    errors = error_re.findall(output)

    if not locations and not errors:
        # Fallback: first 10 lines containing recognisable failure keywords
        keywords = [l for l in output.splitlines()
                    if "Error" in l or "FAILED" in l or "assert" in l.lower()]
        return "\n".join(keywords[:10])

    parts: list[str] = []
    if locations:
        filename, lineno, context = locations[0]
        parts.append(f'File "{filename}", line {lineno}, in {context}')
    if errors:
        parts.append(f"  {errors[0]}")

    return "\n".join(parts)


class RunPipeline:
    """Pipeline that runs the six-stage TDG loop for each task."""

    def __init__(self, artifacts_dir: str = "artifacts/runs"):
        """Initialize the pipeline."""
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        llm = OpenAIClient() if os.getenv("OPENAI_API_KEY") else None
        self.orchestrator = OrchestratorAgent(llm=llm)
        self.developer = DeveloperAgent(llm=llm)
        self.tester = TesterAgent(llm=llm)
        self.failure_analyzer = FailureAnalyzerAgent(llm=llm)
        self.critic = CodeQualityCriticAgent(llm=llm)

    def run(self, user_message: str) -> dict:
        """Execute the six-stage TDG loop for the given user message."""
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "run_id": run_id,
            "task_spec": None,
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
            task_spec = self.orchestrator.assign_task(user_message)
            results["task_spec"] = task_spec
            task_spec_file = run_dir / "task_spec.json"
            task_spec_file.write_text(task_spec.model_dump_json(indent=2))
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

                    # Stage 5b: Code Quality Critic
                    print(f"  \u2192 Code Quality Critic: reviewing for overfitting...")
                    quality_report = self.critic.review(
                        task_spec, current_code_file.read_text()
                    )
                    quality_file = run_dir / f"quality_report_iter{iteration}.json"
                    quality_file.write_text(quality_report.model_dump_json(indent=2))

                    if quality_report.passed:
                        print(f"  \u2713 QUALITY OK \u2014 {quality_report.summary}")
                        break

                    print(f"  \u2717 QUALITY FAIL \u2014 {quality_report.summary}")
                    for flag in quality_report.flags:
                        print(f"         - {flag[:120]}")

                    if iteration < MAX_ITERATIONS:
                        print(f"  \u2192 Sending QualityReport to Developer Agent for clean rewrite...")
                        code_artifact = self.developer.generate_code(
                            task_spec, failure_trace,
                            current_code=current_code_file.read_text(),
                            test_code=test_artifact.content,
                            failure_analysis=None,
                            quality_report=quality_report,
                        )
                        next_code_file = run_dir / f"generated_code_iter{iteration + 1}.py"
                        next_code_file.write_text(code_artifact.content)
                        print(f"  \u2192 Rewritten code saved: {next_code_file.name}")
                    continue

                # Stage 5: parse failures, build FailureTrace, refine code
                failed_tests = self.tester.parse_failures(execution_result)
                feedback = self.tester.review_results(execution_result)
                first_line = feedback.splitlines()[0][:120] if feedback else ""
                print(f"  \u2717 FAILED \u2014 {first_line}")
                print(f"         Failed tests: {', '.join(failed_tests) if failed_tests else 'see output'}")

                # Failure Analyzer: extract structured per-test facts from pytest output
                print(f"  \u2192 Failure Analyzer: extracting structured facts from pytest output...")
                failure_analysis = self.failure_analyzer.analyze(
                    task_spec, execution_result, failed_tests
                )
                analysis_file = run_dir / f"failure_analysis_iter{iteration}.json"
                analysis_file.write_text(failure_analysis.model_dump_json(indent=2))
                print(f"         summary   : {failure_analysis.failure_summary}")
                for sf in failure_analysis.failed_tests[:3]:
                    detail = f"{sf.test_name} [{sf.failure_type}]"
                    if sf.expected and sf.actual:
                        detail += f" expected={sf.expected} actual={sf.actual}"
                    print(f"         - {detail}")

                record = IterationRecord(
                    iteration=iteration,
                    failed_tests=failed_tests,
                    traceback_summary=_extract_traceback(execution_result.output),
                    pytest_output=execution_result.output,
                    code_snapshot=current_code_file.read_text(),
                    exit_code=execution_result.exit_code,
                )
                if failure_trace is None:
                    failure_trace = FailureTrace(history=[record])
                else:
                    failure_trace.history.append(record)

                if iteration < MAX_ITERATIONS:
                    print(f"  \u2192 Sending FailureAnalysis + FailureTrace to Developer Agent...")
                    code_artifact = self.developer.generate_code(
                        task_spec, failure_trace,
                        current_code=code_artifact.content,
                        test_code=test_artifact.content,
                        failure_analysis=failure_analysis,
                    )
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
            tb_str = traceback.format_exc()
            print(f"Pipeline error:\n{tb_str}")
            results["error"] = str(e)

        summary_file = run_dir / "summary.json"
        summary = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "task_description": results["task_spec"].description if results.get("task_spec") else user_message,
            "success": results.get("success", False),
            "iterations": results.get("iterations", 0),
            "execution_status": results["execution_result"].status.value
            if results.get("execution_result") else None,
        }
        summary_file.write_text(json.dumps(summary, indent=2))

        try:
            report_path = ReportGenerator().generate_and_save(run_dir)
            print(f"         \u2514 run_report.md written: {report_path.name}")
        except Exception as report_err:
            print(f"Warning: could not write run_report.md: {report_err}")

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
