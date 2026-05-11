"""Pytest runner for executing tests."""

import shutil
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Optional
from ai_delivery.models.execution_result import ExecutionResult, ExecutionStatus


class PytestRunner:
    """Runner for executing pytest on generated code."""

    def __init__(self, timeout: int = 30):
        """Initialize the pytest runner."""
        self.timeout = timeout

    def run(self, test_code: str, code_path: str) -> ExecutionResult:
        """Run pytest on the given test code."""
        import time
        from datetime import datetime

        start_time = time.time()

        try:
            # Create a temporary directory for the test
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write the test file
                test_file = Path(temp_dir) / "test_generated.py"
                test_file.write_text(test_code)

                # Copy solution module so tests can import it
                if code_path and os.path.exists(code_path):
                    shutil.copy(code_path, Path(temp_dir) / "solution.py")

                # Run pytest
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_file), "-v"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=temp_dir,
                )

                duration = time.time() - start_time

                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.FAILURE,
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode,
                    timestamp=datetime.utcnow(),
                    duration_seconds=duration,
                )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                output="",
                error="Test execution timed out",
                exit_code=-1,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                output="",
                error=str(e),
                exit_code=-1,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
            )

    def run_on_file(self, test_file_path: str) -> ExecutionResult:
        """Run pytest on an existing test file."""
        import time
        from datetime import datetime

        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file_path, "-v"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.FAILURE,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                output="",
                error="Test execution timed out",
                exit_code=-1,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                output="",
                error=str(e),
                exit_code=-1,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
            )
