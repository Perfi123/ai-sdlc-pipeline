import json
import requests as http
from agents.schemas import RequirementOutput, CodeOutput, TestOutput, DeploymentOutput
from agents.prompts import DEPLOYMENT_AGENT_PROMPT
from portkey_client import call_claude
from config import config


def run_deployment_agent(
    requirement: RequirementOutput,
    code: CodeOutput,
    tests: TestOutput,
    open_real_pr: bool = False,
) -> DeploymentOutput:
    """
    Generates PR documentation, and optionally opens a real draft PR on GitHub
    if GITHUB_TOKEN / GITHUB_REPO are configured and open_real_pr=True.
    """
    user_prompt = (
        f"Requirement:\n{requirement.model_dump_json(indent=2)}\n\n"
        f"Code summary: {code.summary}\n"
        f"Filename: {code.filename}\n"
        f"Tests passed: {tests.passed}\n"
        f"Test output: {tests.test_output[:500] if tests.test_output else 'N/A'}"
    )

    raw = call_claude(
        system_prompt=DEPLOYMENT_AGENT_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1200,
        expect_json=True,
    )
    data = json.loads(raw)
    deployment = DeploymentOutput(**data)

    if open_real_pr and config.GITHUB_TOKEN and config.GITHUB_REPO:
        pr_url = _open_draft_pr(deployment, code)
        deployment.pr_url = pr_url
        deployment.deployed = pr_url is not None
    else:
        deployment.deployed = False

    return deployment


def _open_draft_pr(deployment: DeploymentOutput, code: CodeOutput) -> str | None:
    """
    Minimal example of opening a draft PR via GitHub's REST API. This requires
    a branch with the committed change to already exist (left as an extension
    point — see README's production roadmap for full CI/CD wiring).
    """
    try:
        url = f"https://api.github.com/repos/{config.GITHUB_REPO}/pulls"
        headers = {
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "title": deployment.pr_title,
            "body": deployment.pr_description,
            "head": "ai-sdlc-pipeline-change",  # branch must exist
            "base": "main",
            "draft": True,
        }
        resp = http.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 201:
            return resp.json().get("html_url")
        return None
    except Exception:
        return None
