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
        inferred_rules = (
            "\n".join(f"  - {rule}" for rule in analysis.inferred_rules)
            if analysis.inferred_rules
            else "  (none)"
        )
        evidence_lines = []
        if analysis.expected_value:
            evidence_lines.append(f"  expected : {analysis.expected_value}")
        if analysis.actual_value:
            evidence_lines.append(f"  actual   : {analysis.actual_value}")
        if analysis.difference:
            evidence_lines.append(f"  delta    : {analysis.difference}")
        evidence_str = "\n".join(evidence_lines) if evidence_lines else "  (not extracted)"
        analysis_section = (
            "--- FAILURE ANALYSIS (read this first) ---\n"
            f"Category  : {analysis.failure_category} (confidence {analysis.confidence:.2f})\n"
            f"Evidence  :\n{evidence_str}\n\n"
            f"Likely bug: {analysis.likely_bug}\n\n"
            f"Inferred rules:\n{inferred_rules}\n\n"
            f"Patch instruction: {analysis.patch_instruction}\n"
            "--- END FAILURE ANALYSIS ---\n\n"
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

    repair_mode = _get_repair_mode(failure_trace, analysis)

    repair_section = ""
    if repair_mode == "FORCED_PRECISION":
        repair_section = (
            "--- FORCED PRECISION REPAIR MODE ---\n"
            "The same precision test keeps failing across multiple iterations. "
            "The business logic is NOT the problem.\n"
            "Do NOT change discount rules, VIP surcharge, age brackets, condition thresholds, "
            "or any other business rule.\n"
            "ONLY change how the final numeric value is computed:\n"
            "  - Use Decimal for all intermediate arithmetic.\n"
            "  - Convert float inputs to Decimal via str() first: Decimal(str(value)).\n"
            "  - Apply all discounts and surcharges in Decimal.\n"
            "  - Quantize to Decimal('0.01') with ROUND_HALF_UP at the final return statement only.\n"
            "  - Return float(result) to match the task contract.\n"
            "--- END FORCED PRECISION REPAIR MODE ---\n\n"
        )
    elif repair_mode == "PRECISION":
        repair_section = (
            "--- PRECISION REPAIR MODE ---\n"
            "This failure is a decimal precision issue. The business logic is likely correct.\n"
            "Do NOT change discount rules, surcharge rules, condition thresholds, or any "
            "business rule.\n"
            "ONLY fix how the final numeric value is calculated:\n"
            "  - Switch to Decimal arithmetic internally.\n"
            "  - Convert float inputs via Decimal(str(value)).\n"
            "  - Quantize to Decimal('0.01') with ROUND_HALF_UP at the return point only.\n"
            "  - Return float(result).\n"
            "--- END PRECISION REPAIR MODE ---\n\n"
        )
    elif repair_mode == "GENERIC_STUCK":
        repair_section = (
            "--- STUCK FAILURE MODE ---\n"
            "The same tests are failing repeatedly. Do not make another small patch.\n"
            "Reconstruct the relevant implementation directly from the TaskSpec and business rules.\n"
            "Replace the broken logic completely if needed.\n"
            "Use the failed examples as arithmetic constraints.\n"
            "Preserve the structure of the business rules.\n"
            "For example, if the spec defines global weight tiers plus destination surcharges, "
            "do not create separate destination-specific weight tiers. Compute base_cost first, "
            "compute surcharge second, then combine them once.\n"
            "--- END STUCK FAILURE MODE ---\n\n"
        )

    if quality_report is not None and not quality_report.passed:
        preamble = (
            "You are an expert Python developer fixing code that passed tests "
            "but failed quality review.\n\n"
        )
    elif repair_mode == "FORCED_PRECISION":
        preamble = (
            "You are an expert Python developer fixing a decimal precision failure "
            "after repeated failed repairs. Constrained repair only.\n\n"
        )
    elif repair_mode == "PRECISION":
        preamble = (
            "You are an expert Python developer fixing a decimal precision failure.\n\n"
        )
    elif repair_mode == "GENERIC_STUCK":
        preamble = (
            "You are an expert Python developer performing a full logic rewrite "
            "after repeated failed repairs.\n\n"
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
        f"{repair_section}"
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
        "Fix all issues. Follow the TaskSpec, business rules, implementation discipline, "
        "repair mode, quality flags, and failure analysis sections above.\n"
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


def _is_stuck(failure_trace: "FailureTrace") -> bool:
    """Detect whether the same failing test set is repeating.

    This intentionally uses a simple rule:
    if the latest failed test set equals the previous failed test set,
    the repair loop is probably stuck and should switch from patch mode
    to rewrite-from-spec mode.
    """
    if len(failure_trace.history) < 2:
        return False

    latest = failure_trace.history[-1].failed_tests
    previous = failure_trace.history[-2].failed_tests

    return bool(latest) and set(latest) == set(previous)


def _get_repair_mode(
    failure_trace: "FailureTrace",
    analysis: "FailureAnalysis | None",
) -> str:
    """Decide which repair strategy the developer prompt should use.

    Priority order (highest first):
      FORCED_PRECISION — same precision test repeated; strictest constraints, no business logic changes
      PRECISION        — precision failure detected with high confidence; narrow repair now
      GENERIC_STUCK    — repeated failures, non-precision category; full logic rewrite
      NORMAL           — standard refinement

    Keeping _is_stuck() as the internal repetition primitive ensures the stuck
    detection logic lives in one place.
    """
    stuck = _is_stuck(failure_trace)
    is_precision = (
        analysis is not None
        and analysis.failure_category == "precision_rounding_error"
    )
    high_confidence = analysis is not None and analysis.confidence >= 0.8

    if stuck and is_precision:
        return "FORCED_PRECISION"
    if is_precision and high_confidence:
        return "PRECISION"
    if stuck:
        return "GENERIC_STUCK"
    return "NORMAL"