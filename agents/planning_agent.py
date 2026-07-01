import json
from agents.schemas import RequirementOutput, PlanningOutput
from agents.prompts import PLANNING_AGENT_PROMPT
from portkey_client import call_claude


def run_planning_agent(requirement: RequirementOutput) -> PlanningOutput:
    """Turns a structured requirement into a concrete implementation plan."""
    raw = call_claude(
        system_prompt=PLANNING_AGENT_PROMPT,
        user_prompt=f"Structured requirement:\n\n{requirement.model_dump_json(indent=2)}",
        expect_json=True,
    )
    data = json.loads(raw)
    return PlanningOutput(**data)
