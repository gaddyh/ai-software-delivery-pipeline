"""Failure Analyzer agent — converts raw pytest output into structured test failure facts."""

import re
from typing import Optional

from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.failure_analysis import FailureAnalysis, StructuredTestFailure
from ai_delivery.prompts.failure_analyzer_prompts import (
    analyze_failures_prompt,
    FAILURE_ANALYSIS_SCHEMA,
)

_GENERIC_FAILURE = StructuredTestFailure(
    test_name="unknown",
    failure_type="UnknownFailure",
    expected=None,
    actual=None,
    error_message="Could not parse pytest failure details.",
    trace_excerpt="",
)


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
            A FailureAnalysis with one StructuredTestFailure per failing test
            and a plain-English failure_summary.
        """
        if self.llm is not None:
            prompt = analyze_failures_prompt(
                task_spec, failed_tests, execution_result.output
            )
            raw = self.llm.invoke(prompt, schema=FAILURE_ANALYSIS_SCHEMA)
            structured: list[StructuredTestFailure] = []
            for item in raw.get("failed_tests", []):
                structured.append(
                    StructuredTestFailure(
                        test_name=item.get("test_name", "unknown"),
                        failure_type=item.get("failure_type", "UnknownFailure"),
                        expected=item.get("expected") or None,
                        actual=item.get("actual") or None,
                        error_message=item.get("error_message", ""),
                        trace_excerpt=item.get("trace_excerpt", ""),
                    )
                )
            if not structured:
                structured = [_GENERIC_FAILURE]
            return FailureAnalysis(
                failed_tests=structured,
                failure_summary=raw.get("failure_summary", ""),
            )

        # ── Regex fallback (no LLM) ────────────────────────────────────────
        return self._regex_analyze(execution_result.output, failed_tests)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _regex_analyze(self, pytest_output: str, failed_tests: list[str]) -> FailureAnalysis:
        """Best-effort deterministic analysis when no LLM is available."""
        error_lines = re.findall(r"^E\s{1,3}(.+)$", pytest_output, re.MULTILINE)

        # Build a brief trace excerpt from the first location + error lines
        location_lines = re.findall(
            r"^\s{0,4}\S+\.py:\d+:.+$", pytest_output, re.MULTILINE
        )
        trace_excerpt = "\n".join(
            (location_lines[:2] if location_lines else []) + error_lines[:3]
        )

        structured: list[StructuredTestFailure] = []

        for test_name in failed_tests:
            # Detect failure type from error lines
            failure_type = "AssertionError"
            for line in error_lines:
                if "Error" in line and "assert" not in line.lower():
                    failure_type = line.split(":")[0].strip()
                    break

            expected: Optional[str] = None
            actual: Optional[str] = None
            error_message = ""

            for line in error_lines:
                m = re.search(r"assert\s+(.+?)\s*==\s*(.+)", line)
                if m:
                    actual = m.group(1).strip()
                    expected = m.group(2).strip()
                    error_message = line.strip()
                    break

            if not error_message and error_lines:
                error_message = error_lines[0].strip()

            structured.append(
                StructuredTestFailure(
                    test_name=test_name,
                    failure_type=failure_type,
                    expected=expected,
                    actual=actual,
                    error_message=error_message,
                    trace_excerpt=trace_excerpt,
                )
            )

        if not structured:
            generic = StructuredTestFailure(
                test_name="unknown",
                failure_type="UnknownFailure",
                expected=None,
                actual=None,
                error_message="Could not parse pytest failure details.",
                trace_excerpt=pytest_output[:2000],
            )
            structured = [generic]

        count = len(structured)
        summary_parts = [f"{count} test{'s' if count != 1 else ''} failed."]
        for f in structured[:3]:
            if f.expected and f.actual:
                summary_parts.append(
                    f"{f.test_name} expected {f.expected} but got {f.actual}."
                )
            elif f.error_message:
                summary_parts.append(f"{f.test_name}: {f.error_message[:100]}")
        failure_summary = " ".join(summary_parts)

        return FailureAnalysis(
            failed_tests=structured,
            failure_summary=failure_summary,
        )
