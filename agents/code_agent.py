import json
from typing import Optional
from agents.schemas import PlanningOutput, CodeOutput
from agents.prompts import CODE_AGENT_PROMPT_TEMPLATE, CODE_FIX_PROMPT_SUFFIX
from portkey_client import call_claude


def run_code_agent(
    plan: PlanningOutput,
    language: str,
    previous_code: Optional[CodeOutput] = None,
    failure_reason: Optional[str] = None,
) -> CodeOutput:
    """
    Generates source code from an implementation plan.

    If previous_code + failure_reason are provided, this is a retry: the prompt
    includes the failing test feedback so the agent fixes its own mistake.
    """
    system_prompt = CODE_AGENT_PROMPT_TEMPLATE.format(language=language)
    user_prompt = f"Implementation plan:\n\n{plan.model_dump_json(indent=2)}"

    if previous_code and failure_reason:
        system_prompt += CODE_FIX_PROMPT_SUFFIX.format(failure_reason=failure_reason)
        user_prompt += f"\n\nPrevious (failing) code:\n\n{previous_code.code}"

    raw = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=3000,
        expect_json=True,
    )
    data = json.loads(raw)
    return CodeOutput(**data)
