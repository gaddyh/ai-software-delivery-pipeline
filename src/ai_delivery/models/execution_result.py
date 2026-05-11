"""Execution result model."""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """Status of execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    SKIPPED = "skipped"


class ExecutionResult(BaseModel):
    """Result of executing a generated artifact."""

    status: ExecutionStatus = Field(..., description="Execution status")
    output: str = Field(default="", description="Standard output from execution")
    error: str = Field(default="", description="Error output from execution")
    exit_code: int = Field(default=0, description="Exit code from execution")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float = Field(default=0.0, description="Execution duration in seconds")
