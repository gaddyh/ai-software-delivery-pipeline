"""Example script to run the shipping pipeline once."""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.pipeline.run import RunPipeline


def main():
    """Run the shipping pipeline once."""
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Using placeholder implementation.")

    # Define the task
    task_spec = TaskSpec(
        raw_requirement="Create a simple Python function that calculates the factorial of a number",
        function_name="factorial",
        function_signature="def factorial(n: int) -> int",
        module_name="solution",
        description="Create a simple Python function that calculates the factorial of a number",
        constraints=["Use recursion or iteration", "No external libraries"],
        success_criteria=["Correctly calculates factorial for positive integers", "Handles edge case of 0"],
        edge_cases=["n = 0", "n = 1", "negative numbers"],
    )

    # Initialize the pipeline
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts/runs")
    pipeline = RunPipeline(artifacts_dir=artifacts_dir)

    # Run the pipeline
    print("=" * 60)
    print("AI Software Delivery Pipeline")
    print("=" * 60)
    results = pipeline.run(task_spec)

    # Print summary
    print("\n" + "=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    print(f"Run ID: {results['run_id']}")
    print(f"Task: {task_spec.description}")
    print(f"Success: {results['success']}")
    print(f"Iterations: {results.get('iterations', 'N/A')}")

    if results.get("execution_result"):
        print(f"Execution Status: {results['execution_result'].status.value}")
        print(f"Exit Code: {results['execution_result'].exit_code}")
        if results["execution_result"].output:
            print(f"\nOutput:\n{results['execution_result'].output}")
        if results["execution_result"].error:
            print(f"\nError:\n{results['execution_result'].error}")

    # Show run history
    print("\n" + "=" * 60)
    print("Run History")
    print("=" * 60)
    history = pipeline.get_run_history()
    for run in history[-5:]:  # Show last 5 runs
        print(f"  {run['run_id']}: {run['task_description']} - {run['execution_status']}")


if __name__ == "__main__":
    main()
