"""Generates a Markdown run report from the artifacts produced by RunPipeline."""

import json
import re
from pathlib import Path


class ReportGenerator:
    """Reads artifacts from a run directory and assembles a Markdown report.

    No LLM calls are made — this is pure file reading and string assembly.
    """

    def generate(self, run_dir: Path) -> str:
        """Build and return the full Markdown report for *run_dir*.

        Args:
            run_dir: Path to a single run directory (e.g. artifacts/runs/20260512_002755).

        Returns:
            The complete Markdown string.
        """
        run_dir = Path(run_dir)
        summary = self._load_json(run_dir / "summary.json")
        task_spec_data = self._load_json(run_dir / "task_spec.json") if (run_dir / "task_spec.json").exists() else {}
        iterations = summary.get("iterations", 0)

        sections: list[str] = []

        # ── Header ────────────────────────────────────────────────────────────
        outcome = "✅ SUCCESS" if summary.get("success") else "❌ FAILURE"
        sections.append(f"# Run Report — `{summary.get('run_id', run_dir.name)}`\n")
        sections.append(
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| **Outcome** | {outcome} |\n"
            f"| **Iterations** | {iterations} |\n"
            f"| **Timestamp** | `{summary.get('timestamp', 'unknown')}` |\n"
            f"| **Task** | {summary.get('task_description', '—')} |\n"
        )

        # ── Task Spec (class/function + methods) ─────────────────────────────
        class_name = task_spec_data.get("class_name", "")
        methods = task_spec_data.get("methods", [])
        if class_name or methods:
            sections.append("\n## Task Spec\n")
            if class_name:
                sections.append(
                    f"| Field | Value |\n"
                    f"|-------|-------|\n"
                    f"| **Type** | Class |\n"
                    f"| **Class** | `{class_name}` |\n"
                    f"| **Module** | `{task_spec_data.get('module_name', 'solution')}` |\n"
                )
                if methods:
                    sections.append("\n**Methods:**\n")
                    sections.append("| Signature |")
                    sections.append("|-----------|")
                    for m in methods:
                        sections.append(f"| `{m}` |")
                    sections.append("")
            else:
                sections.append(
                    f"| Field | Value |\n"
                    f"|-------|-------|\n"
                    f"| **Type** | Module functions |\n"
                    f"| **Module** | `{task_spec_data.get('module_name', 'solution')}` |\n"
                )
                if methods:
                    sections.append("\n**Functions:**\n")
                    sections.append("| Signature |")
                    sections.append("|-----------|")
                    for m in methods:
                        sections.append(f"| `{m}` |")
                    sections.append("")

        # ── Business Rules (from task_spec if saved) ──────────────────────────
        business_rules = task_spec_data.get("business_rules", [])
        if business_rules:
            sections.append("\n## Business Rules\n")
            if isinstance(business_rules, list):
                sections.append("| Rule | Condition |")
                sections.append("|------|-----------|")
                for r in business_rules:
                    if isinstance(r, dict):
                        name = r.get("name", "")
                        rule = r.get("rule", "")
                        sections.append(f"| {name} | `{rule}` |")
                sections.append("")
            elif isinstance(business_rules, dict):
                sections.append("```json\n" + json.dumps(business_rules, indent=2) + "\n```\n")

        # ── Test Suite ────────────────────────────────────────────────────────
        test_file = run_dir / "test_suite.py"
        if test_file.exists():
            test_names = re.findall(r"^def (test_\w+)", test_file.read_text(), re.MULTILINE)
            sections.append(f"\n## Test Suite ({len(test_names)} tests)\n")
            for name in test_names:
                sections.append(f"- `{name}`")
            sections.append("")

        # ── Iteration Timeline ────────────────────────────────────────────────
        sections.append("\n## Iteration Timeline\n")
        for i in range(1, iterations + 1):
            exec_result = self._load_json(run_dir / f"execution_result_iter{i}.json")
            status = exec_result.get("status", "unknown")
            passed = status == "success"
            icon = "✅" if passed else "❌"

            sections.append(f"### Iteration {i} — {icon} {'PASSED' if passed else 'FAILED'}\n")

            if not passed:
                failure_analysis = self._load_json(run_dir / f"failure_analysis_iter{i}.json")
                failed_tests = failure_analysis.get("failed_tests", [])
                if failed_tests:
                    sections.append("**Failed tests:**")
                    for t in failed_tests:
                        sections.append(f"- `{t}`")
                    sections.append("")

                likely_bug = failure_analysis.get("likely_bug", "")
                patch = failure_analysis.get("patch_instruction", "")
                if likely_bug:
                    sections.append(f"**Failure Analyzer diagnosis:** {likely_bug}\n")
                if patch:
                    sections.append(f"**Patch instruction:** {patch}\n")

                inferred = failure_analysis.get("inferred_rules", [])
                if inferred:
                    sections.append("**Inferred rules:**")
                    for rule in inferred:
                        sections.append(f"- {rule}")
                    sections.append("")

            # Quality critic report (only present when tests passed)
            quality_file = run_dir / f"quality_report_iter{i}.json"
            if quality_file.exists():
                qr = self._load_json(quality_file)
                q_passed = qr.get("passed", True)
                q_icon = "✅" if q_passed else "⚠️"
                sections.append(f"**Code Quality Critic:** {q_icon} {qr.get('summary', '')}\n")
                for flag in qr.get("flags", []):
                    sections.append(f"- ⚠️ {flag}")
                if qr.get("flags"):
                    sections.append("")

        # ── Final Implementation ──────────────────────────────────────────────
        final_code_file = run_dir / f"generated_code_iter{iterations}.py"
        if not final_code_file.exists():
            # Fall back to latest available iteration
            candidates = sorted(run_dir.glob("generated_code_iter*.py"))
            final_code_file = candidates[-1] if candidates else None

        if final_code_file and final_code_file.exists():
            sections.append("\n## Final Implementation\n")
            sections.append("```python")
            sections.append(final_code_file.read_text().rstrip())
            sections.append("```\n")

        # ── Quality Sign-off ──────────────────────────────────────────────────
        # Find the last quality report (the one that passed)
        last_qr_file = None
        for i in range(iterations, 0, -1):
            qf = run_dir / f"quality_report_iter{i}.json"
            if qf.exists():
                last_qr_file = qf
                break

        if last_qr_file:
            last_qr = self._load_json(last_qr_file)
            passed = last_qr.get("passed", False)
            icon = "✅" if passed else "❌"
            sections.append("## Quality Sign-off\n")
            sections.append(f"{icon} **{last_qr.get('summary', '')}**\n")
        elif summary.get("success"):
            sections.append("## Quality Sign-off\n")
            sections.append("✅ **No quality issues detected.**\n")

        return "\n".join(sections)

    def generate_and_save(self, run_dir: Path) -> Path:
        """Generate the report and write it to *run_dir*/run_report.md.

        Returns:
            The path to the written file.
        """
        run_dir = Path(run_dir)
        report = self.generate(run_dir)
        out = run_dir / "run_report.md"
        out.write_text(report)
        return out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> dict:
        """Load JSON from *path*, returning an empty dict on any error."""
        try:
            return json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
