"""Prompt builders for DeveloperAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.task_spec import TaskSpec
    from ai_delivery.models.failure_trace import FailureTrace
    from ai_delivery.models.failure_analysis import FailureAnalysis
    from ai_delivery.models.quality_report import QualityReport


def initial_code_prompt(task_spec: "TaskSpec") -> str:
    """Prompt for the first code-generation attempt (no prior failures)."""
    constraints = (
        "\n".join(f"  - {c}" for c in task_spec.constraints)
        if task_spec.constraints
        else "  (none)"
    )
    edge_cases = (
        "\n".join(f"  - {e}" for e in task_spec.edge_cases)
        if task_spec.edge_cases
        else "  (none)"
    )
    return (
        "You are an expert Python developer. "
        "Write a clean, correct Python implementation for the following task.\n\n"
        f"Task: {task_spec.description}\n"
        f"Function signature: {task_spec.function_signature}\n"
        f"Module name (for imports): {task_spec.module_name}\n\n"
        f"Constraints:\n{constraints}\n\n"
        f"Edge cases to handle:\n{edge_cases}\n\n"
        "Return a JSON object with a single key 'code' containing the full Python source. "
        "The file must be self-contained and importable as a module named "
        f"'{task_spec.module_name}'. Do not include test code."
    )


def refine_code_prompt(
    task_spec: "TaskSpec",
    current_code: str,
    failure_trace: "FailureTrace",
    test_code: str = "",
    analysis: "FailureAnalysis | None" = None,
    quality_report: "QualityReport | None" = None,
) -> str:
    """Prompt for a refinement attempt informed by prior test failures."""
    latest = failure_trace.latest()
    prior_count = len(failure_trace.history)

    failed_tests_str = (
        "\n".join(f"  - {t}" for t in latest.failed_tests)
        if latest and latest.failed_tests
        else "  (see pytest output below)"
    )
    traceback_summary = latest.traceback_summary if latest else ""

    # Include full pytest output for every prior attempt so the developer
    # can see what it already tried and what each attempt broke.
    all_outputs = "\n\n".join(
        f"[Iteration {r.iteration}]\n{r.pytest_output}"
        for r in failure_trace.history
    )

    test_section = (
        f"--- TEST SUITE (fixed, do not modify) ---\n{test_code}\n\n"
        if test_code
        else ""
    )

    analysis_section = ""
    if analysis is not None:
        rules = "\n".join(f"  - {r}" for r in analysis.inferred_rules)
        analysis_section = (
            f"--- FAILURE ANALYSIS (read this first) ---\n"
            f"Likely bug: {analysis.likely_bug}\n\n"
            f"Inferred rules:\n{rules}\n\n"
            f"Patch instruction: {analysis.patch_instruction}\n"
            f"--- END FAILURE ANALYSIS ---\n\n"
        )

    quality_section = ""
    if quality_report is not None and not quality_report.passed:
        flags_str = "\n".join(f"  - {f}" for f in quality_report.flags)
        quality_section = (
            f"--- CODE QUALITY FLAGS (tests passed but code is overfitted) ---\n"
            f"Verdict: {quality_report.summary}\n\n"
            f"Issues found:\n{flags_str}\n\n"
            "You MUST rewrite the logic to implement the real business rules correctly. "
            "Do NOT use exact-value special cases, negative adjustments, or hack comments.\n"
            f"--- END CODE QUALITY FLAGS ---\n\n"
        )

    preamble = (
        "You are an expert Python developer fixing overfitted code.\n\n"
        if quality_report is not None and not quality_report.passed
        else "You are an expert Python developer fixing failing tests.\n\n"
    )

    return (
        f"{preamble}"
        f"Task: {task_spec.description}\n"
        f"Function signature: {task_spec.function_signature}\n\n"
        f"{test_section}"
        f"{quality_section}"
        f"{analysis_section}"
        f"--- CURRENT CODE (iteration {prior_count}) ---\n"
        f"{current_code}\n\n"
        f"--- FAILING TESTS (latest) ---\n"
        f"{failed_tests_str}\n\n"
        f"--- TRACEBACK (latest) ---\n"
        f"{traceback_summary}\n\n"
        f"--- FULL PYTEST OUTPUT (all {prior_count} attempt(s)) ---\n"
        f"{all_outputs}\n\n"
        "Fix all issues. Follow the CODE QUALITY FLAGS and FAILURE ANALYSIS sections above. "
        "Return a JSON object with a single key 'code' containing the corrected full Python "
        f"source, importable as '{task_spec.module_name}'. Do not include test code."
    )
