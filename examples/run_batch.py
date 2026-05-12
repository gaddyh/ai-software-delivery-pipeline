"""Batch runner: execute the AI delivery pipeline for a list of user messages."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from ai_delivery.pipeline.run import RunPipeline

# Import benchmark user messages
sys.path.insert(0, str(Path(__file__).parent.parent))
from benchmark_user_messages import mvp1_benchmark_set, harder_mvp1_benchmark_set

_BENCHMARK_SETS = {
    "base": mvp1_benchmark_set,
    "hard": harder_mvp1_benchmark_set,
}

# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI delivery pipeline benchmark.")
    parser.add_argument(
        "--benchmark",
        choices=["base", "hard"],
        default="base",
        help="Which benchmark set to run: 'base' (mvp1_benchmark_set) or 'hard' (harder_mvp1_benchmark_set). Default: base.",
    )
    args = parser.parse_args()

    user_messages = _BENCHMARK_SETS[args.benchmark]
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts/runs")
    pipeline = RunPipeline(artifacts_dir=artifacts_dir)

    total = len(user_messages)
    results: list[dict] = []

    print("=" * 60)
    print(f"Batch Run [{args.benchmark}] — {total} task(s)")
    print("=" * 60)

    for i, message in enumerate(user_messages, start=1):
        print(f"\n[{i}/{total}] Starting task...")
        try:
            result = pipeline.run(message)
        except Exception as exc:
            print(f"[{i}/{total}] ✗ PIPELINE ERROR — {exc}")
            results.append({
                "index": i,
                "run_id": "—",
                "task": message[:60].replace("\n", " ") + "…",
                "success": False,
                "iterations": "—",
                "error": str(exc),
            })
            continue

        task_spec = result.get("task_spec")
        task_label = task_spec.description if task_spec else message[:60] + "…"
        icon = "✓" if result["success"] else "✗"
        iters = result.get("iterations", "?")
        print(f"[{i}/{total}] {icon} {task_label[:55]} — {iters} iter(s)")

        results.append({
            "index": i,
            "run_id": result.get("run_id", "—"),
            "task": task_label,
            "success": result["success"],
            "iterations": iters,
            "error": None,
        })

    # ── Summary table ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Batch Summary")
    print("=" * 60)
    passed = sum(1 for r in results if r["success"])
    print(f"Passed: {passed}/{total}\n")

    col_id   = max(len(r["run_id"]) for r in results)
    col_task = min(max(len(r["task"]) for r in results), 52)
    header = f"  {'#':<3}  {'Run ID':<{col_id}}  {'Task':<{col_task}}  {'OK':>4}  {'Iter':>4}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in results:
        ok    = "✓" if r["success"] else "✗"
        task  = r["task"][:col_task]
        print(f"  {r['index']:<3}  {r['run_id']:<{col_id}}  {task:<{col_task}}  {ok:>4}  {str(r['iterations']):>4}")

    print()


if __name__ == "__main__":
    main()
