"""Example script to run the shipping pipeline once."""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from ai_delivery.pipeline.run import RunPipeline


def main():
    """Run the shipping pipeline once."""
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Using placeholder implementation.")

    user_message = (
        "Hey, I need a Python function for our checkout service. "
        "The function should be called calculate_shipping and take three arguments: "
        "cart_total as a float, package_weight as a float, and destination_zone as a string. "
        "Return the final shipping cost as a float. "
        ""
        "Here are the rules. If cart_total is greater than $150, shipping is free, no matter "
        "how heavy the package is or where it is going. "
        ""
        "If the cart total is $150 or less, calculate shipping by weight first: "
        "packages up to and including 2 kg cost $5, packages over 2 kg and up to and including "
        "5 kg cost $10, and packages over 5 kg cost $18. "
        ""
        "Then apply a destination surcharge. For destination_zone='local', add $0. "
        "For destination_zone='regional', add $4. "
        "For destination_zone='international', add $12. "
        ""
        "There is one special rule: international packages over 10 kg are not allowed, "
        "so raise a ValueError in that case. "
        ""
        "Also raise a ValueError if cart_total is negative, package_weight is negative, "
        "or destination_zone is not one of: local, regional, international. "
        ""
        "Important boundary cases: cart_total exactly 150 is not free shipping. "
        "package_weight exactly 2 kg uses the $5 tier. "
        "package_weight exactly 5 kg uses the $10 tier. "
        "package_weight exactly 10 kg is still allowed for international shipping. "
        ""
        "Round the returned shipping cost to two decimal places."
    )

    # Initialize the pipeline
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts/runs")
    pipeline = RunPipeline(artifacts_dir=artifacts_dir)

    # Run the pipeline
    print("=" * 60)
    print("AI Software Delivery Pipeline")
    print("=" * 60)
    results = pipeline.run(user_message)

    # Print summary
    print("\n" + "=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    print(f"Run ID: {results['run_id']}")
    task_spec = results.get("task_spec")
    print(f"Task: {task_spec.description if task_spec else user_message}")
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
