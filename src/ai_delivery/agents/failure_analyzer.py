"""Failure Analyzer agent — converts raw pytest output into structured test failure facts."""

import re
from typing import Optional

from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.execution_result import ExecutionResult
from ai_delivery.models.failure_analysis import (
    BlamedArtifact,
    FailureAnalysis,
    FailureStage,
    FailureType,
    RecommendedAction,
    StructuredTestFailure,
)
from ai_delivery.prompts.failure_analyzer_prompts import (
    analyze_failures_prompt,
    FAILURE_ANALYSIS_SCHEMA,
)


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------

def normalize_test_name(name: str) -> str:
    """Strip file prefix and parametrize suffix; return a clean test function name."""
    name = name.strip()
    name = name.split("::")[-1]
    name = name.split("[")[0]
    name = name.replace(" ", "_")
    return name[:120] or "unknown_test"


def normalize_value(val: str | None) -> str:
    """Trim whitespace and surrounding quotes; cap length for stable signatures."""
    if val is None:
        return ""
    return str(val).strip().strip("'\"")[:120]


def normalize_exception(exc: str | None) -> str:
    """Keep only the bare exception class name (strip module path and message)."""
    if not exc:
        return ""
    exc = str(exc).strip().split(":")[0].split(".")[-1]
    return exc[:80]


def build_failure_signature(failure: StructuredTestFailure) -> str:
    """Build a stable, readable signature for a single test failure.

    Format: stage|type|artifact|test_name|expected|actual|exception
    """
    return "|".join([
        failure.failure_stage.value,
        failure.failure_type.value,
        failure.blamed_artifact.value,
        normalize_test_name(failure.test_name),
        normalize_value(failure.expected),
        normalize_value(failure.actual),
        normalize_exception(failure.raw_exception_type),
    ])


def is_numeric_precision_failure(expected: str | None, actual: str | None) -> bool:
    """Return True when expected and actual differ only by floating-point representation."""
    try:
        e = float(str(expected))
        a = float(str(actual))
        return abs(e - a) <= 1e-6 and str(expected) != str(actual)
    except (TypeError, ValueError):
        return False


def _extract_raw_exception(pytest_output: str) -> Optional[str]:
    """Pull the first recognisable exception class name from pytest output."""
    m = re.search(r"\b(\w+Error|\w+Exception|SyntaxError|IndentationError)\b", pytest_output)
    return m.group(1) if m else None


_GENERIC_FAILURE = StructuredTestFailure(
    test_name="unknown",
    failure_stage=FailureStage.UNKNOWN,
    failure_type=FailureType.UNKNOWN,
    raw_exception_type=None,
    expected=None,
    actual=None,
    error_message="Could not parse pytest failure details.",
    trace_excerpt="",
    blamed_artifact=BlamedArtifact.UNKNOWN,
    confidence=0.0,
    evidence=[],
    failure_signature="unknown|unknown|unknown|unknown|||",
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
            return self._llm_analyze(task_spec, execution_result, failed_tests)

        # ── Regex fallback (no LLM) ────────────────────────────────────────
        return self._regex_analyze(execution_result.output, failed_tests)

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------

    def _llm_analyze(
        self,
        task_spec: TaskSpec,
        execution_result: ExecutionResult,
        failed_tests: list[str],
    ) -> FailureAnalysis:
        """Invoke the LLM for semantic classification, then enrich with deterministic fields."""
        pytest_output = execution_result.output
        prompt = analyze_failures_prompt(task_spec, failed_tests, pytest_output)
        raw = self.llm.invoke(prompt, schema=FAILURE_ANALYSIS_SCHEMA)  # type: ignore[union-attr]

        # Determine failure stage from collection error signals
        is_collection = bool(
            re.search(r"ERROR collecting|collection error", pytest_output, re.IGNORECASE)
            or ("SyntaxError" in pytest_output and not failed_tests)
            or ("IndentationError" in pytest_output and not failed_tests)
        )
        global_stage = FailureStage.TEST_COLLECTION if is_collection else FailureStage.TEST_EXECUTION

        structured: list[StructuredTestFailure] = []
        for item in raw.get("failed_tests", []):
            raw_exc = _extract_raw_exception(item.get("trace_excerpt", "") + item.get("error_message", ""))

            expected = item.get("expected") or None
            actual = item.get("actual") or None

            # Parse LLM enum fields with safe fallbacks
            try:
                f_type = FailureType(item.get("failure_type", FailureType.UNKNOWN.value))
            except ValueError:
                f_type = FailureType.UNKNOWN

            try:
                blamed = BlamedArtifact(item.get("blamed_artifact", BlamedArtifact.UNKNOWN.value))
            except ValueError:
                blamed = BlamedArtifact.UNKNOWN

            confidence = float(item.get("confidence", 0.5))

            # Deterministic override: numeric precision beats LLM classification
            if is_numeric_precision_failure(expected, actual):
                f_type = FailureType.NUMERIC_PRECISION
                blamed = BlamedArtifact.IMPLEMENTATION
                confidence = max(confidence, 0.9)

            failure = StructuredTestFailure(
                test_name=item.get("test_name", "unknown"),
                failure_stage=global_stage,
                failure_type=f_type,
                raw_exception_type=raw_exc,
                expected=expected,
                actual=actual,
                error_message=item.get("error_message", ""),
                trace_excerpt=item.get("trace_excerpt", ""),
                blamed_artifact=blamed,
                confidence=confidence,
                evidence=item.get("evidence", []),
                failure_signature="",  # filled below
            )
            failure.failure_signature = build_failure_signature(failure)
            structured.append(failure)

        if not structured:
            structured = [_GENERIC_FAILURE]

        iteration_sig = "||".join(sorted(f.failure_signature for f in structured))

        # Parse top-level LLM fields with safe fallbacks
        try:
            primary_type = FailureType(raw.get("primary_failure_type", FailureType.UNKNOWN.value))
        except ValueError:
            primary_type = FailureType.UNKNOWN

        try:
            primary_artifact = BlamedArtifact(raw.get("primary_blamed_artifact", BlamedArtifact.UNKNOWN.value))
        except ValueError:
            primary_artifact = BlamedArtifact.UNKNOWN

        try:
            action = RecommendedAction(raw.get("recommended_action", RecommendedAction.UNKNOWN.value))
        except ValueError:
            action = RecommendedAction.UNKNOWN

        return FailureAnalysis(
            failed_tests=structured,
            failure_summary=raw.get("failure_summary", ""),
            primary_failure_type=primary_type,
            primary_blamed_artifact=primary_artifact,
            recommended_action=action,
            should_modify_code=bool(raw.get("should_modify_code", True)),
            should_modify_tests=bool(raw.get("should_modify_tests", False)),
            should_review_spec=bool(raw.get("should_review_spec", False)),
            iteration_failure_signature=iteration_sig,
            routing_reason=raw.get("routing_reason", ""),
            lesson=raw.get("lesson", ""),
        )

    # ------------------------------------------------------------------
    # Regex fallback
    # ------------------------------------------------------------------

    def _regex_analyze(self, pytest_output: str, failed_tests: list[str]) -> FailureAnalysis:
        """Best-effort deterministic analysis when no LLM is available."""
        # ── 1. Collection-level errors first ──────────────────────────────
        if "SyntaxError" in pytest_output:
            return self._collection_error_result(
                pytest_output, FailureType.TEST_SYNTAX_ERROR,
                routing_reason="Pytest failed during collection: SyntaxError in test file."
            )
        if "IndentationError" in pytest_output:
            return self._collection_error_result(
                pytest_output, FailureType.TEST_INDENTATION_ERROR,
                routing_reason="Pytest failed during collection: IndentationError in test file."
            )
        if "ImportError" in pytest_output or "ModuleNotFoundError" in pytest_output:
            return self._collection_error_result(
                pytest_output, FailureType.TEST_IMPORT_ERROR,
                routing_reason=(
                    "Pytest failed during collection: import error. "
                    # Conservative MVP assumption: collection-time import failures are treated as
                    # test-suite failures. Later we can inspect whether the import comes from
                    # solution.py or test_generated.py.
                    "Treated as test-suite failure (MVP conservative assumption)."
                )
            )

        # ── 2. Normal per-test extraction ─────────────────────────────────
        error_lines = re.findall(r"^E\s{1,3}(.+)$", pytest_output, re.MULTILINE)

        location_lines = re.findall(
            r"^\s{0,4}\S+\.py:\d+:.+$", pytest_output, re.MULTILINE
        )
        trace_excerpt = "\n".join(
            (location_lines[:2] if location_lines else []) + error_lines[:3]
        )

        raw_exc_global = _extract_raw_exception(pytest_output)

        structured: list[StructuredTestFailure] = []

        for test_name in failed_tests:
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

            # Routing defaults
            f_type = FailureType.UNKNOWN
            blamed = BlamedArtifact.UNKNOWN
            action = RecommendedAction.REPAIR_IMPLEMENTATION
            modify_code = True
            modify_tests = False
            confidence = 0.4

            # Deterministic numeric precision override
            if is_numeric_precision_failure(expected, actual):
                f_type = FailureType.NUMERIC_PRECISION
                blamed = BlamedArtifact.IMPLEMENTATION
                action = RecommendedAction.APPLY_MINIMAL_NUMERIC_REPAIR
                modify_code = True
                modify_tests = False
                confidence = 0.9

            failure = StructuredTestFailure(
                test_name=test_name,
                failure_stage=FailureStage.TEST_EXECUTION,
                failure_type=f_type,
                raw_exception_type=raw_exc_global,
                expected=expected,
                actual=actual,
                error_message=error_message,
                trace_excerpt=trace_excerpt,
                blamed_artifact=blamed,
                confidence=confidence,
                evidence=[],
                failure_signature="",  # filled below
            )
            failure.failure_signature = build_failure_signature(failure)
            structured.append(failure)

        if not structured:
            generic = StructuredTestFailure(
                test_name="unknown",
                failure_stage=FailureStage.UNKNOWN,
                failure_type=FailureType.UNKNOWN,
                raw_exception_type=raw_exc_global,
                expected=None,
                actual=None,
                error_message="Could not parse pytest failure details.",
                trace_excerpt=pytest_output[:2000],
                blamed_artifact=BlamedArtifact.UNKNOWN,
                confidence=0.0,
                evidence=[],
                failure_signature="",
            )
            generic.failure_signature = build_failure_signature(generic)
            structured = [generic]
            action = RecommendedAction.REPAIR_IMPLEMENTATION
            modify_code = True
            modify_tests = False
            confidence = 0.4
            blamed = BlamedArtifact.UNKNOWN

        # Derive top-level routing from the first (dominant) failure
        dominant = structured[0]
        primary_type = dominant.failure_type
        primary_artifact = dominant.blamed_artifact

        # Use action/flags from the dominant failure's routing
        if len(structured) == 1 or all(f.failure_type == dominant.failure_type for f in structured):
            final_action = action
            final_modify_code = modify_code
            final_modify_tests = modify_tests
        else:
            final_action = RecommendedAction.REPAIR_IMPLEMENTATION
            final_modify_code = True
            final_modify_tests = False

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

        iteration_sig = "||".join(sorted(f.failure_signature for f in structured))

        return FailureAnalysis(
            failed_tests=structured,
            failure_summary=failure_summary,
            primary_failure_type=primary_type,
            primary_blamed_artifact=primary_artifact,
            recommended_action=final_action,
            should_modify_code=final_modify_code,
            should_modify_tests=final_modify_tests,
            should_review_spec=False,
            iteration_failure_signature=iteration_sig,
            routing_reason="",
            lesson="",
        )

    def _collection_error_result(
        self,
        pytest_output: str,
        failure_type: FailureType,
        routing_reason: str,
    ) -> FailureAnalysis:
        """Produce a FailureAnalysis for a pytest collection-phase failure."""
        raw_exc = _extract_raw_exception(pytest_output)

        error_lines = re.findall(r"^E\s{1,3}(.+)$", pytest_output, re.MULTILINE)
        trace_lines = re.findall(r"^\s{0,4}\S+\.py:\d+:.+$", pytest_output, re.MULTILINE)
        trace_excerpt = "\n".join((trace_lines[:2] if trace_lines else []) + error_lines[:3])
        error_message = error_lines[0].strip() if error_lines else pytest_output[:300]

        if failure_type == FailureType.TEST_SYNTAX_ERROR:
            action = RecommendedAction.REPAIR_TEST_SUITE
            confidence = 0.95
        elif failure_type == FailureType.TEST_INDENTATION_ERROR:
            action = RecommendedAction.REPAIR_TEST_SUITE
            confidence = 0.95
        else:
            action = RecommendedAction.REPAIR_TEST_SUITE
            confidence = 0.85

        failure = StructuredTestFailure(
            test_name="pytest_collection",
            failure_stage=FailureStage.TEST_COLLECTION,
            failure_type=failure_type,
            raw_exception_type=raw_exc,
            expected=None,
            actual=None,
            error_message=error_message,
            trace_excerpt=trace_excerpt,
            blamed_artifact=BlamedArtifact.TEST_SUITE,
            confidence=confidence,
            evidence=[],
            failure_signature="",  # filled below
        )
        failure.failure_signature = build_failure_signature(failure)

        iteration_sig = failure.failure_signature

        return FailureAnalysis(
            failed_tests=[failure],
            failure_summary=f"Pytest collection failed: {failure_type.value}. {error_message[:200]}",
            primary_failure_type=failure_type,
            primary_blamed_artifact=BlamedArtifact.TEST_SUITE,
            recommended_action=action,
            should_modify_code=False,
            should_modify_tests=True,
            should_review_spec=False,
            iteration_failure_signature=iteration_sig,
            routing_reason=routing_reason,
            lesson="",
        )
