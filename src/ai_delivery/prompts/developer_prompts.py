"""Prompt builders for DeveloperAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_delivery.models.failure_analysis import FailureAnalysis
    from ai_delivery.models.failure_trace import FailureTrace
    from ai_delivery.models.quality_report import QualityReport
    from ai_delivery.models.task_spec import TaskSpec

from ai_delivery.prompts.task_context import format_task_context


def initial_code_prompt(task_spec: "TaskSpec") -> str:
    """Prompt for the first code-generation attempt with no prior failures."""
    artifact_instruction = (
        f"Implement a class named '{task_spec.class_name}' with exactly the public methods listed. "
        "No CLI entry point. Do not include tests."
        if task_spec.is_class_task
        else "Implement the module-level function(s) listed. Do not include tests."
    )

    return (
        "You are an expert Python developer.\n"
        "Write a clean, correct Python implementation for the following task.\n\n"
        f"Task: {task_spec.description}\n\n"
        f"{format_task_context(task_spec)}\n\n"
        f"{_format_business_rules(task_spec)}\n\n"
        f"{_format_list('Constraints', task_spec.constraints)}\n\n"
        f"{_format_list('Edge cases to handle', task_spec.edge_cases)}\n\n"
        f"{_implementation_discipline()}\n\n"
        f"{artifact_instruction}\n\n"
        "Return a JSON object with a single key 'code' containing the full Python source. "
        "The file must be self-contained and importable as a module named "
        f"'{task_spec.module_name}'."
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
        f"[Iteration {record.iteration}]\n{record.pytest_output}"
        for record in failure_trace.history
    )

    test_section = (
        f"--- TEST SUITE (fixed, do not modify) ---\n{test_code}\n\n"
        if test_code
        else ""
    )

    analysis_section = ""
    if analysis is not None:
        modify_code_str = "yes" if analysis.should_modify_code else "no"
        modify_tests_str = "yes" if analysis.should_modify_tests else "no"

        if analysis.should_modify_code:
            repair_guidance = (
                "Only make the smallest implementation change needed for this failure type.\n"
                "Do not rewrite unrelated business rules."
            )
        else:
            repair_guidance = (
                "The failure appears to be in the test suite.\n"
                "If you must return code, return the current implementation unchanged\n"
                "unless there is clear implementation evidence in the pytest output."
            )

        policy_lines = [
            "--- REPAIR POLICY ---",
            f"Recommended action  : {analysis.recommended_action.value}",
            f"Primary failure type: {analysis.primary_failure_type.value}",
            f"Blamed artifact     : {analysis.primary_blamed_artifact.value}",
            f"Modify code         : {modify_code_str}",
            f"Modify tests        : {modify_tests_str}",
        ]
        if analysis.routing_reason:
            policy_lines.append(f"Routing reason      : {analysis.routing_reason}")
        if analysis.lesson:
            policy_lines.append(f"Lesson              : {analysis.lesson}")
        policy_lines.append("")
        policy_lines.append(repair_guidance)
        policy_lines.append("--- END REPAIR POLICY ---")

        failure_lines: list[str] = []
        for f in analysis.failed_tests:
            line = f"  [{f.failure_type.value}] {f.test_name}"
            if f.expected and f.actual:
                line += f"\n    expected : {f.expected}\n    actual   : {f.actual}"
            if f.error_message:
                line += f"\n    error    : {f.error_message}"
            if f.trace_excerpt:
                line += f"\n    trace    :\n      " + f.trace_excerpt.replace("\n", "\n      ")
            failure_lines.append(line)
        failures_str = "\n\n".join(failure_lines) if failure_lines else "  (none)"

        analysis_section = (
            "\n".join(policy_lines) + "\n\n"
            "--- STRUCTURED FAILURE ANALYSIS ---\n"
            "The failure analysis is factual, not prescriptive.\n"
            "You are responsible for identifying the root cause and applying a minimal general fix.\n\n"
            f"Summary: {analysis.failure_summary}\n\n"
            f"Per-test details:\n{failures_str}\n"
            "--- END STRUCTURED FAILURE ANALYSIS ---\n\n"
        )

    quality_section = ""
    if quality_report is not None and not quality_report.passed:
        flags_str = (
            "\n".join(f"  - {flag}" for flag in quality_report.flags)
            if quality_report.flags
            else "  (none)"
        )
        quality_section = (
            "--- CODE QUALITY FLAGS (tests passed but code is not acceptable) ---\n"
            f"Verdict: {quality_report.summary}\n\n"
            f"Issues found:\n{flags_str}\n\n"
            "You MUST rewrite the logic to implement the real business rules correctly. "
            "Do not use exact-value special cases, negative adjustments, extra rules, "
            "or hack comments.\n"
            "--- END CODE QUALITY FLAGS ---\n\n"
        )

    if quality_report is not None and not quality_report.passed:
        preamble = (
            "You are an expert Python developer fixing code that passed tests "
            "but failed quality review.\n\n"
        )
    else:
        preamble = "You are an expert Python developer fixing failing tests.\n\n"

    return (
        f"{preamble}"
        f"Task: {task_spec.description}\n\n"
        f"{format_task_context(task_spec)}\n\n"
        f"{_format_business_rules(task_spec)}\n\n"
        f"{_format_list('Constraints', task_spec.constraints)}\n\n"
        f"{_format_list('Edge cases to handle', task_spec.edge_cases)}\n\n"
        f"{_implementation_discipline()}\n\n"
        f"{quality_section}"
        f"{analysis_section}"
        f"--- CURRENT CODE (iteration {prior_count}) ---\n"
        f"{current_code}\n\n"
        f"{test_section}"
        f"--- FAILING TESTS (latest) ---\n"
        f"{failed_tests_str}\n\n"
        f"--- TRACEBACK (latest) ---\n"
        f"{traceback_summary}\n\n"
        f"--- FULL PYTEST OUTPUT (all {prior_count} attempt(s)) ---\n"
        f"{all_outputs}\n\n"
        "Fix all issues. Do not modify tests. Do not change public API signatures. "
        "Prefer minimal general fixes grounded in the TaskSpec and business rules.\n"
        "Return a JSON object with a single key 'code' containing the corrected full Python "
        f"source, importable as '{task_spec.module_name}'. Do not include test code."
    )


def _format_list(title: str, values: list[str]) -> str:
    """Format a simple list section for prompts."""
    body = "\n".join(f"  - {value}" for value in values) if values else "  (none)"
    return f"{title}:\n{body}"


def _format_business_rules(task_spec: "TaskSpec") -> str:
    """Format named business rules for prompts."""
    if not task_spec.business_rules:
        return "Business rules:\n  (none)"

    lines: list[str] = []

    for rule in task_spec.business_rules:
        name = getattr(rule, "name", "")
        condition = getattr(rule, "rule", "")

        if name and condition:
            lines.append(f"  - {name}: {condition}")
        elif condition:
            lines.append(f"  - {condition}")
        else:
            lines.append(f"  - {rule}")

    return "Business rules:\n" + "\n".join(lines)


def _implementation_discipline() -> str:
    """Rules that keep the developer grounded in the TaskSpec."""
    return (
        "Implementation discipline:\n"
        "  - Implement the TaskSpec and business rules exactly as written.\n"
        "  - Do not invent additional business rules, constants, coupons, tiers, pricing models, classes, or special cases.\n"
        "  - Do not add behavior unless it is grounded in the TaskSpec, business rules, constraints, edge cases, or tests.\n"
        "  - If the business rules are expressed as separate concepts, preserve that separation in code.\n"
        "  - For example: if the spec defines global weight tiers plus destination surcharges, compute base_cost from weight first, compute surcharge from destination second, then return base_cost + surcharge.\n"
        "  - Do not create destination-specific weight tiers unless the TaskSpec explicitly asks for them.\n"
        "  - Do not hardcode individual test cases.\n"
        "  - Do not include comments such as 'fix for test', 'adjusted to satisfy test', or similar hack comments."
    )

