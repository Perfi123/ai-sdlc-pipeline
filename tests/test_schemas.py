"""
Lightweight tests that don't require API access — validate the JSON contracts
between agents are well-formed. Run with: python -m pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.schemas import RequirementOutput, PlanningOutput, CodeOutput, TestOutput, DeploymentOutput


def test_requirement_output_schema():
    req = RequirementOutput(
        title="Password reset",
        description="Allow users to reset password via email",
        acceptance_criteria=["User receives reset email", "Link expires after 1 hour"],
        edge_cases=["Invalid email", "Expired token reused"],
        priority="high",
        story_points=5,
    )
    assert req.title == "Password reset"
    assert len(req.acceptance_criteria) == 2


def test_planning_output_schema():
    plan = PlanningOutput(
        architectural_rationale="Use token-based reset flow",
        files_to_create_or_modify=["auth/reset.py"],
        function_or_class_signatures=["def reset_password(email: str) -> bool"],
    )
    assert plan.dependencies == []


def test_code_output_schema():
    code = CodeOutput(
        language="python",
        filename="auth/reset.py",
        code="def reset_password(email):\n    pass",
        summary="Implements password reset",
    )
    assert code.language == "python"


def test_test_output_schema():
    t = TestOutput(test_code="import unittest", executed=True, passed=True, test_output="OK")
    assert t.passed is True


def test_deployment_output_schema():
    d = DeploymentOutput(
        pr_title="feat: password reset",
        pr_description="Adds password reset via email",
        changelog_entry="Add password reset",
    )
    assert d.deployed is False


if __name__ == "__main__":
    test_requirement_output_schema()
    test_planning_output_schema()
    test_code_output_schema()
    test_test_output_schema()
    test_deployment_output_schema()
    print("All schema tests passed.")
