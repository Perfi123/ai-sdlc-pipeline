"""
The JSON contracts every agent must produce. Keeping these explicit means any
agent can be swapped for a better prompt/model later without breaking the
pipeline, as long as it still returns this shape.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RequirementOutput(BaseModel):
    title: str
    description: str
    acceptance_criteria: List[str]
    edge_cases: List[str]
    priority: str = Field(description="One of: low, medium, high, critical")
    story_points: int


class PlanningOutput(BaseModel):
    architectural_rationale: str
    files_to_create_or_modify: List[str]
    function_or_class_signatures: List[str]
    data_model_notes: Optional[str] = ""
    dependencies: List[str] = []


class CodeOutput(BaseModel):
    language: str
    filename: str
    code: str
    summary: str
    assumptions: List[str] = []


class TestOutput(BaseModel):
    test_code: str
    executed: bool
    passed: Optional[bool] = None
    test_output: Optional[str] = ""
    failure_reason: Optional[str] = ""


class DeploymentOutput(BaseModel):
    pr_title: str
    pr_description: str
    changelog_entry: str
    pr_url: Optional[str] = None
    deployed: bool = False
