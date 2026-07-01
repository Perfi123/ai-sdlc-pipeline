"""
The shared state object passed between every node in the LangGraph pipeline.
Using a TypedDict (LangGraph's expected state shape) with optional fields that
get filled in as the pipeline progresses.
"""
from typing import TypedDict, Optional, List
from agents.schemas import RequirementOutput, PlanningOutput, CodeOutput, TestOutput, DeploymentOutput


class PipelineState(TypedDict, total=False):
    # inputs
    user_story: str
    language: str
    open_real_pr: bool

    # stage outputs
    requirement: Optional[RequirementOutput]
    plan: Optional[PlanningOutput]
    code: Optional[CodeOutput]
    tests: Optional[TestOutput]
    deployment: Optional[DeploymentOutput]

    # control flow
    retry_count: int
    max_retries: int
    status_log: List[str]
    error: Optional[str]
