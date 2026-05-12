"""Run the isolated calculate_ticket_price benchmark task."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from ai_delivery.pipeline.run import RunPipeline

TICKET_TASK = (
    "Build a Python function called calculate_ticket_price for an event checkout. "
    "It should take base_price: float, age: int, is_student: bool, and is_vip: bool. "
    "Start with the base price. Children under 12 get 50 percent off. "
    "Students get 20 percent off. VIP tickets add a fixed 30 dollar fee after discounts. "
    "If someone is both a child and a student, apply only the child discount, not both. "
    "If base_price is negative or age is negative, raise ValueError. "
    "Return the final price as a float rounded to 2 decimal places."
)


def main() -> None:
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts/runs")
    pipeline = RunPipeline(artifacts_dir=artifacts_dir)
    print("=" * 60)
    print("Isolated task: calculate_ticket_price")
    print("=" * 60)
    result = pipeline.run(TICKET_TASK)
    print("\n" + "=" * 60)
    print(f"Final result : {'PASS' if result['success'] else 'FAIL'}")
    print(f"Iterations   : {result.get('iterations', '?')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
