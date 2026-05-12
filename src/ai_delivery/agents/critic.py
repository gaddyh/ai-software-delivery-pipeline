"""Code Quality Critic agent — detects overfitting and hardcoded test-case hacks."""

import re
from typing import Optional

from ai_delivery.llm.base import LLMClient
from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.quality_report import QualityReport
from ai_delivery.prompts.critic_prompts import review_code_prompt, QUALITY_REPORT_SCHEMA


class CodeQualityCriticAgent:
    """Reviews generated code for overfitting patterns after tests pass.

    The critic runs only when the test suite is green.  If it finds quality
    issues it returns a QualityReport with passed=False and a list of flags,
    which are fed back to the Developer Agent for one more refinement pass.
    """

    def __init__(self, model_name: str = "gpt-4o", llm: Optional[LLMClient] = None):
        """Initialise the critic."""
        self.model_name = model_name
        self.llm = llm

    def review(self, task_spec: TaskSpec, code: str) -> QualityReport:
        """Analyse *code* for overfitting and hardcoded hacks.

        Args:
            task_spec: The original task specification including business_rules.
            code: The generated Python source to review.

        Returns:
            A QualityReport.  passed=True means the code is clean.
        """
        if self.llm is not None:
            prompt = review_code_prompt(task_spec, code)
            raw = self.llm.invoke(prompt, schema=QUALITY_REPORT_SCHEMA)
            return QualityReport(
                passed=raw.get("passed", True),
                flags=raw.get("flags", []),
                summary=raw.get("summary", ""),
            )

        return self._regex_review(code)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _regex_review(self, code: str) -> QualityReport:
        """Best-effort static analysis when no LLM is available."""
        flags: list[str] = []

        # Hack comments
        hack_comment = re.search(
            r"#.*\b(adjust|workaround|to meet expected|hack|to satisfy)\b",
            code,
            re.IGNORECASE,
        )
        if hack_comment:
            flags.append(f"Suspicious comment: {hack_comment.group(0).strip()}")

        # Exact-value equality checks on numeric inputs
        exact_checks = re.findall(r"\b\w+\s*==\s*\d+\.?\d*", code)
        for check in exact_checks:
            flags.append(f"Exact-value special case: {check.strip()}")

        # Negative literal assignments (e.g. surcharge = -2.5)
        neg_literals = re.findall(r"=\s*-\d+\.?\d*", code)
        for lit in neg_literals:
            flags.append(f"Negative literal assignment: {lit.strip()}")

        passed = len(flags) == 0
        summary = (
            "Code passes quality review."
            if passed
            else f"Found {len(flags)} potential overfitting pattern(s)."
        )
        return QualityReport(passed=passed, flags=flags, summary=summary)
