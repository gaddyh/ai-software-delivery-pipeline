"""Failure Analyzer agent — converts raw pytest output into structured patch instructions."""

import re
from typing import Optional

from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.failure_analysis import FailureAnalysis
from ai_delivery.prompts.failure_analyzer_prompts import (
    analyze_failures_prompt,
    FAILURE_ANALYSIS_SCHEMA,
)

_PRECISION_TEST_KEYWORDS = re.compile(
    r"round|decimal|precision|two_decimal|2_decimal", re.IGNORECASE
)
_PRECISION_ASSERT_KEYWORDS = re.compile(r"round|decimal", re.IGNORECASE)


class FailureAnalyzerAgent:
    """Agent that reads pytest output and produces a structured FailureAnalysis.

    When an LLM is available the analysis is generated via a schema-enforced
    OpenAI call.  Without an LLM the agent falls back to regex-based extraction
    so the pipeline keeps running without an API key.
    """

    def __init__(self, model_name: str = "gpt-4o", llm: Optional[LLMClient] = None):
        """Initialise the agent."""
        self.model_name = model_name
        self.llm = llm

    def analyze(
        self,
        task_spec: TaskSpec,
        execution_result: ExecutionResult,
        failed_tests: list[str],
    ) -> FailureAnalysis:
        """Produce a FailureAnalysis from the latest execution result.

        Args:
            task_spec: The task the code is supposed to implement.
            execution_result: The result of the most recent pytest run.
            failed_tests: Pre-parsed list of failing test names.

        Returns:
            A FailureAnalysis with structured evidence, category, and confidence fields.
        """
        if self.llm is not None:
            prompt = analyze_failures_prompt(
                task_spec, failed_tests, execution_result.output
            )
            raw = self.llm.invoke(prompt, schema=FAILURE_ANALYSIS_SCHEMA)
            return FailureAnalysis(
                failed_tests=raw.get("failed_tests", failed_tests),
                inferred_rules=raw.get("inferred_rules", []),
                likely_bug=raw.get("likely_bug", ""),
                patch_instruction=raw.get("patch_instruction", ""),
                expected_value=raw.get("expected_value") or None,
                actual_value=raw.get("actual_value") or None,
                difference=raw.get("difference") or None,
                failure_category=raw.get("failure_category", "unknown"),
                confidence=float(raw.get("confidence", 0.0)),
            )

        # ── Stub fallback (no LLM) ─────────────────────────────────────────
        return self._regex_analyze(execution_result.output, failed_tests)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _regex_analyze(self, pytest_output: str, failed_tests: list[str]) -> FailureAnalysis:
        """Best-effort deterministic analysis when no LLM is available."""
        # Extract lines starting with "E " (pytest error lines)
        error_lines = re.findall(r"^E\s{1,3}(.+)$", pytest_output, re.MULTILINE)

        # Pull out assert-equality failures: "assert X == Y" or "AssertionError: X != Y"
        inferred_rules: list[str] = []
        expected_value: Optional[str] = None
        actual_value: Optional[str] = None
        difference: Optional[str] = None

        for line in error_lines:
            m = re.search(r"assert\s+(.+?)\s*==\s*(.+)", line)
            if m:
                got, expected = m.group(1).strip(), m.group(2).strip()
                inferred_rules.append(f"Expected {expected}, got {got}")
                if expected_value is None:
                    actual_value = got
                    expected_value = expected

        if not inferred_rules and error_lines:
            inferred_rules = [e.strip() for e in error_lines[:3]]

        # ── Multi-signal precision detection ─────────────────────────────
        failure_category, confidence = self._detect_precision(
            failed_tests, error_lines, actual_value, expected_value
        )

        if difference is None and actual_value and expected_value:
            try:
                delta = abs(float(actual_value) - float(expected_value))
                difference = f"~{delta:.2e}"
            except (ValueError, TypeError):
                pass

        likely_bug = (
            f"Implementation produces wrong output for: {', '.join(failed_tests[:2])}"
            if failed_tests
            else "Unknown defect — inspect pytest output."
        )
        patch_instruction = (
            "Fix the logic so that each failing assertion produces its expected value. "
            "Check condition ordering carefully."
        )

        return FailureAnalysis(
            failed_tests=failed_tests,
            inferred_rules=inferred_rules,
            likely_bug=likely_bug,
            patch_instruction=patch_instruction,
            expected_value=expected_value,
            actual_value=actual_value,
            difference=difference,
            failure_category=failure_category,
            confidence=confidence,
        )

    def _detect_precision(
        self,
        failed_tests: list[str],
        error_lines: list[str],
        actual_value: Optional[str],
        expected_value: Optional[str],
    ) -> tuple[str, float]:
        """Count multi-signal evidence for precision_rounding_error.

        Returns (failure_category, confidence).
        """
        signals = 0

        # Signal 1: test name contains precision-related keyword
        if any(_PRECISION_TEST_KEYWORDS.search(t) for t in failed_tests):
            signals += 1

        # Signal 2: assertion text contains rounding/decimal keyword
        if any(_PRECISION_ASSERT_KEYWORDS.search(line) for line in error_lines):
            signals += 1

        # Signal 3: actual and expected are numerically close floats
        if actual_value and expected_value:
            try:
                delta = abs(float(actual_value) - float(expected_value))
                if delta < 0.01:
                    signals += 1
            except (ValueError, TypeError):
                pass

        # Signal 4: actual value has excessive decimal places (> 4 significant digits after decimal)
        if actual_value:
            m = re.search(r"\.\d{5,}", actual_value)
            if m:
                signals += 1

        if signals >= 2:
            return "precision_rounding_error", 0.8
        if signals == 1:
            return "precision_rounding_error", 0.5
        return "unknown", 0.0
