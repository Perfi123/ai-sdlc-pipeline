import json
from agents.schemas import RequirementOutput
from agents.prompts import REQUIREMENT_AGENT_PROMPT
from portkey_client import call_claude


def run_requirement_agent(user_story: str) -> RequirementOutput:
    """Turns a raw user story into a structured, testable requirement."""
    raw = call_claude(
        system_prompt=REQUIREMENT_AGENT_PROMPT,
        user_prompt=f"Raw user story / feature idea:\n\n{user_story}",
        expect_json=True,
    )
    data = json.loads(raw)
    return RequirementOutput(**data)
