"""Standalone script: generate run_report.md for any run directory.

Usage:
    python3 examples/generate_report.py                   # latest run
    python3 examples/generate_report.py 20260512_002755   # specific run ID
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from ai_delivery.reporting.report_generator import ReportGenerator


def main() -> None:
    load_dotenv()

    artifacts_dir = Path(os.getenv("ARTIFACTS_DIR", "artifacts/runs"))

    if len(sys.argv) > 1:
        run_id = sys.argv[1]
        run_dir = artifacts_dir / run_id
        if not run_dir.is_dir():
            print(f"Error: run directory not found: {run_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default to the most recent run dir that has a summary.json
        candidates = sorted(
            (d for d in artifacts_dir.iterdir() if d.is_dir() and (d / "summary.json").exists()),
            key=lambda d: d.name,
        )
        if not candidates:
            print("Error: no completed runs found in artifacts/runs", file=sys.stderr)
            sys.exit(1)
        run_dir = candidates[-1]

    print(f"Generating report for run: {run_dir.name}")
    report_path = ReportGenerator().generate_and_save(run_dir)
    print(f"Report written: {report_path}")
    print()
    print(report_path.read_text())


if __name__ == "__main__":
    main()
