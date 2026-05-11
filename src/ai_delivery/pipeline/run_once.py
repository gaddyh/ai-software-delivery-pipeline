"""Single-run pipeline for shipping software."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.agents.orchestrator import OrchestratorAgent
from ai_delivery.agents.developer import DeveloperAgent
from ai_delivery.agents.tester import TesterAgent


class RunOncePipeline:
    """Pipeline that runs the software delivery process once."""

    def __init__(self, artifacts_dir: str = "artifacts/runs"):
        """Initialize the pipeline."""
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.orchestrator = OrchestratorAgent()
        self.developer = DeveloperAgent()
        self.tester = TesterAgent()

    def run(self, task_spec: TaskSpec) -> dict:
        """Run the pipeline once for the given task specification."""
        print(f"Starting pipeline for: {task_spec.description}")

        # Create a run-specific directory
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
        }

        try:
            # Step 1: Generate code
            print("Step 1: Generating code...")
            code_artifact = self.developer.generate_code(task_spec)
            results["code_artifact"] = code_artifact

            # Save generated code
            code_file = run_dir / "generated_code.py"
            code_file.write_text(code_artifact.content)
            print(f"Code saved to: {code_file}")

            # Step 2: Generate tests
            print("Step 2: Generating tests...")
            test_artifact = self.tester.generate_tests(code_artifact.content)
            results["test_artifact"] = test_artifact

            # Save generated tests
            test_file = run_dir / "test_generated.py"
            test_file.write_text(test_artifact.content)
            print(f"Tests saved to: {test_file}")

            # Step 3: Execute tests
            print("Step 3: Executing tests...")
            execution_result = self.tester.execute_tests(
                test_artifact, str(code_file)
            )
            results["execution_result"] = execution_result

            # Save execution result
            result_file = run_dir / "execution_result.json"
            result_file.write_text(execution_result.model_dump_json(indent=2))
            print(f"Execution result saved to: {result_file}")

            # Step 4: Validate result
            print("Step 4: Validating result...")
            success = self.orchestrator.validate_result(code_artifact, execution_result)
            results["success"] = success

            if success:
                print("Pipeline completed successfully!")
            else:
                print("Pipeline completed with failures.")

        except Exception as e:
            print(f"Pipeline error: {e}")
            results["error"] = str(e)

        # Save run summary
        summary_file = run_dir / "summary.json"
        import json

        summary = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "task_description": task_spec.description,
            "success": results.get("success", False),
            "execution_status": results.get("execution_result").status.value
            if results.get("execution_result")
            else None,
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
                    import json

                    with open(summary_file) as f:
                        history.append(json.load(f))
        return history
