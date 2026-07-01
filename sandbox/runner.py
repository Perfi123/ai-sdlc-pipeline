"""
Executes generated tests in a restricted subprocess sandbox.

Production note: for a real production deployment this should run inside a
locked-down Docker container (no network, read-only filesystem except a tmp
dir, strict CPU/memory/time limits) rather than a bare subprocess. The
subprocess approach here is sufficient for a capstone demo but is called out
explicitly in the README as a hardening item before real production use.

Currently only Python execution is implemented. Other languages return
executed=False with a note that execution isn't wired up yet — this keeps
the contract honest rather than silently faking results.
"""
import os
import subprocess
import tempfile


PYTHON_TIMEOUT_SECONDS = 15


def run_python_tests(source_code: str, test_code: str) -> dict:
    """
    Writes source_code to solution.py and test_code to test_solution.py in a
    temp directory, then runs the tests via `python -m unittest` as a
    subprocess with a timeout. Returns a dict with passed/output/error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        solution_path = os.path.join(tmpdir, "solution.py")
        test_path = os.path.join(tmpdir, "test_solution.py")

        with open(solution_path, "w") as f:
            f.write(source_code)
        with open(test_path, "w") as f:
            f.write(test_code)

        try:
            result = subprocess.run(
                ["python", "-m", "unittest", "test_solution", "-v"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=PYTHON_TIMEOUT_SECONDS,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return {
                "executed": True,
                "passed": False,
                "output": "",
                "error": f"Test execution timed out after {PYTHON_TIMEOUT_SECONDS}s.",
            }

        passed = result.returncode == 0
        return {
            "executed": True,
            "passed": passed,
            "output": result.stdout,
            "error": "" if passed else result.stderr,
        }


def run_tests(language: str, source_code: str, test_code: str) -> dict:
    """Dispatches to the right sandbox runner based on language."""
    if language.lower() == "python":
        return run_python_tests(source_code, test_code)

    # Extension point: add Java (compile + JUnit in docker), TypeScript (ts-node + Jest), etc.
    return {
        "executed": False,
        "passed": None,
        "output": "",
        "error": (
            f"Automated execution for '{language}' is not wired up in this capstone build. "
            f"Test code was generated and should be reviewed/run manually, or extended in "
            f"sandbox/runner.py."
        ),
    }
