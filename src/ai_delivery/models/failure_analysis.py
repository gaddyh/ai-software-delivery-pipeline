"""Structured failure intelligence produced from pytest output."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FailureStage(str, Enum):
    """Where the failure happened."""

    TEST_COLLECTION = "test_collection"
    TEST_EXECUTION = "test_execution"
    QUALITY_REVIEW = "quality_review"
    PIPELINE_ERROR = "pipeline_error"
    UNKNOWN = "unknown"


class FailureType(str, Enum):
    """Normalized failure category used for routing."""

    TEST_SYNTAX_ERROR = "test_syntax_error"
    TEST_INDENTATION_ERROR = "test_indentation_error"
    TEST_IMPORT_ERROR = "test_import_error"
    TEST_COLLECTION_ERROR = "test_collection_error"

    NUMERIC_PRECISION = "numeric_precision"
    ASSERTION_MISMATCH = "assertion_mismatch"
    UNEXPECTED_EXCEPTION = "unexpected_exception"
    MISSING_EXCEPTION = "missing_exception"

    SPEC_AMBIGUITY = "spec_ambiguity"
    IMPLEMENTATION_LOGIC_ERROR = "implementation_logic_error"
    SPEC_TEST_CONFLICT = "spec_test_conflict"
    TEST_EXPECTATION_NOT_GROUNDED = "test_expectation_not_grounded"
    UNKNOWN = "unknown"


class BlamedArtifact(str, Enum):
    """Which artifact probably needs repair."""

    IMPLEMENTATION = "implementation"
    TEST_SUITE = "test_suite"
    TASK_SPEC = "task_spec"
    SPEC_OR_TEST_EXPECTATION = "spec_or_test_expectation"
    UNKNOWN = "unknown"


class RecommendedAction(str, Enum):
    """What the pipeline should do next."""

    REPAIR_IMPLEMENTATION = "repair_implementation"
    REPAIR_TEST_SUITE = "repair_test_suite"
    REVIEW_SPEC_AND_TESTS = "review_spec_and_tests"
    REVIEW_TEST_GROUNDING = "review_test_grounding"
    APPLY_MINIMAL_NUMERIC_REPAIR = "apply_minimal_numeric_repair"
    STOP_AND_ESCALATE = "stop_and_escalate"
    UNKNOWN = "unknown"


class StructuredTestFailure(BaseModel):
    """Factual record of a single failing test or collection error."""

    test_name: str = Field(
        description="Name of the failing test, or collection-level identifier if no test ran."
    )

    failure_stage: FailureStage = Field(
        description="Where the failure occurred: collection, execution, quality review, etc."
    )

    failure_type: FailureType = Field(
        description="Normalized failure category."
    )

    raw_exception_type: Optional[str] = Field(
        default=None,
        description="Original exception type from pytest, e.g. AssertionError, ValueError, SyntaxError."
    )

    expected: Optional[str] = Field(
        default=None,
        description="Expected value from the assertion, if extractable."
    )

    actual: Optional[str] = Field(
        default=None,
        description="Actual value produced by the code, if extractable."
    )

    error_message: str = Field(
        description="The assertion or error message text."
    )

    trace_excerpt: str = Field(
        description="Relevant snippet of the stack trace or pytest output."
    )

    blamed_artifact: BlamedArtifact = Field(
        default=BlamedArtifact.UNKNOWN,
        description="Artifact most likely responsible for the failure."
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the classification and artifact attribution."
    )

    evidence: list[str] = Field(
        default_factory=list,
        description="Short evidence snippets supporting the classification."
    )

    failure_signature: str = Field(
        description="Stable normalized signature used to detect repeated failures."
    )


class FailureAnalysis(BaseModel):
    """Structured facts and routing hints extracted from a pytest run."""

    failed_tests: list[StructuredTestFailure] = Field(
        description="One entry per failing test or collection-level failure."
    )

    failure_summary: str = Field(
        description="Concise plain-English overview of the failure."
    )

    primary_failure_type: FailureType = Field(
        default=FailureType.UNKNOWN,
        description="The dominant failure type for this iteration."
    )

    primary_blamed_artifact: BlamedArtifact = Field(
        default=BlamedArtifact.UNKNOWN,
        description="The artifact most likely responsible for the dominant failure."
    )

    recommended_action: RecommendedAction = Field(
        default=RecommendedAction.UNKNOWN,
        description="Recommended next pipeline action."
    )

    should_modify_code: bool = Field(
        default=True,
        description="Whether the next repair should modify implementation code."
    )

    should_modify_tests: bool = Field(
        default=False,
        description="Whether the next repair should modify the generated test suite."
    )

    should_review_spec: bool = Field(
        default=False,
        description="Whether the spec/test relationship should be reviewed for ambiguity."
    )

    iteration_failure_signature: str = Field(
        description="Combined normalized signature for this iteration, used for stuck detection."
    )

    routing_reason: str = Field(
        default="",
        description="Local explanation for why this routing decision was made (per-iteration)."
    )

    lesson: str = Field(
        default="",
        description="Reusable lesson learned from this failure."
    )