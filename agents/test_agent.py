import json
from agents.schemas import RequirementOutput, CodeOutput, TestOutput
from agents.prompts import TEST_AGENT_PROMPT_TEMPLATE
from portkey_client import call_claude
from sandbox.runner import run_tests


def run_test_agent(requirement: RequirementOutput, code: CodeOutput) -> TestOutput:
    """Generates tests for the produced code, then executes them in the sandbox."""
    system_prompt = TEST_AGENT_PROMPT_TEMPLATE.format(language=code.language)
    user_prompt = (
        f"Acceptance criteria:\n{json.dumps(requirement.acceptance_criteria, indent=2)}\n\n"
        f"Edge cases to cover:\n{json.dumps(requirement.edge_cases, indent=2)}\n\n"
        f"IMPORTANT: regardless of any filename/path mentioned anywhere else, the code below will "
        f"be saved AS solution.py and your test file MUST import from it using "
        f"'from solution import ...' (or 'import solution'). Do not import from any other path.\n\n"
        f"Code under test ({code.language}):\n\n{code.code}"
    )

    raw = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=2000,
        expect_json=True,
    )
    data = json.loads(raw)
    test_code = data["test_code"]

    exec_result = run_tests(code.language, code.code, test_code)

    return TestOutput(
        test_code=test_code,
        executed=exec_result["executed"],
        passed=exec_result["passed"],
        test_output=exec_result["output"],
        failure_reason=exec_result["error"],
    )
