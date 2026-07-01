"""
The LangGraph state machine wiring Requirement -> Planning -> Code -> Test ->
Deployment, with a retry edge: if tests fail, loop back to the Code Agent
(with the failure reason) up to `max_retries` times before giving up.

Run directly for a CLI demo:
    python -m orchestrator.graph --story "..." --language python
"""
import argparse
import json
import sys

from langgraph.graph import StateGraph, END

from orchestrator.state import PipelineState
from agents.requirement_agent import run_requirement_agent
from agents.planning_agent import run_planning_agent
from agents.code_agent import run_code_agent
from agents.test_agent import run_test_agent
from agents.deployment_agent import run_deployment_agent
from config import config


def node_requirement(state: PipelineState) -> PipelineState:
    state["status_log"].append("Requirement Agent: analyzing user story...")
    state["requirement"] = run_requirement_agent(state["user_story"])
    state["status_log"].append("Requirement Agent: done.")
    return state


def node_planning(state: PipelineState) -> PipelineState:
    state["status_log"].append("Planning Agent: drafting implementation plan...")
    state["plan"] = run_planning_agent(state["requirement"])
    state["status_log"].append("Planning Agent: done.")
    return state


def node_code(state: PipelineState) -> PipelineState:
    retry = state.get("retry_count", 0)
    if retry == 0:
        state["status_log"].append(f"Code Agent: generating {state['language']} code...")
        state["code"] = run_code_agent(state["plan"], state["language"])
    else:
        state["status_log"].append(f"Code Agent: fixing code after test failure (attempt {retry + 1})...")
        failure = state["tests"].failure_reason if state.get("tests") else "Unknown failure"
        state["code"] = run_code_agent(
            state["plan"], state["language"], previous_code=state["code"], failure_reason=failure
        )
    state["status_log"].append("Code Agent: done.")
    return state


def node_test(state: PipelineState) -> PipelineState:
    state["status_log"].append("Test Agent: generating and executing tests...")
    state["tests"] = run_test_agent(state["requirement"], state["code"])
    if state["tests"].executed:
        result = "PASSED" if state["tests"].passed else "FAILED"
        state["status_log"].append(f"Test Agent: tests {result}.")
        if not state["tests"].passed:
            state["retry_count"] = state.get("retry_count", 0) + 1
    else:
        state["status_log"].append("Test Agent: tests generated (execution not supported for this language).")
    return state


def node_deployment(state: PipelineState) -> PipelineState:
    state["status_log"].append("Deployment Agent: preparing PR...")
    state["deployment"] = run_deployment_agent(
        state["requirement"], state["code"], state["tests"], open_real_pr=state.get("open_real_pr", False)
    )
    state["status_log"].append("Deployment Agent: done.")
    return state


def route_after_test(state: PipelineState) -> str:
    tests = state["tests"]

    if not tests.executed:
        return "deploy"

    if tests.passed:
        return "deploy"

    if state.get("retry_count", 0) > state.get("max_retries", config.MAX_TEST_RETRIES):
        state["status_log"].append(
            f"Max retries ({state.get('max_retries')}) reached. Proceeding to deployment with failing tests flagged."
        )
        return "deploy"

    return "retry"


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("requirement_stage", node_requirement)
    graph.add_node("planning_stage", node_planning)
    graph.add_node("code_stage", node_code)
    graph.add_node("test_stage", node_test)
    graph.add_node("deployment_stage", node_deployment)

    graph.set_entry_point("requirement_stage")
    graph.add_edge("requirement_stage", "planning_stage")
    graph.add_edge("planning_stage", "code_stage")
    graph.add_edge("code_stage", "test_stage")

    graph.add_conditional_edges(
        "test_stage",
        route_after_test,
        {"retry": "code_stage", "deploy": "deployment_stage"},
    )

    graph.add_edge("deployment_stage", END)

    return graph.compile()


pipeline_app = build_graph()


def run_pipeline(user_story: str, language: str = "python", open_real_pr: bool = False) -> PipelineState:
    initial_state: PipelineState = {
        "user_story": user_story,
        "language": language,
        "open_real_pr": open_real_pr,
        "retry_count": 0,
        "max_retries": config.MAX_TEST_RETRIES,
        "status_log": [],
    }
    final_state = pipeline_app.invoke(initial_state)
    return final_state


def _print_result(state: PipelineState):
    print("\n".join(state["status_log"]))
    print("\n" + "=" * 60)
    print("REQUIREMENT:", state["requirement"].model_dump_json(indent=2))
    print("\nPLAN:", state["plan"].model_dump_json(indent=2))
    print("\nCODE SUMMARY:", state["code"].summary)
    print("\nCODE:\n", state["code"].code)
    print("\nTESTS PASSED:", state["tests"].passed)
    print("\nTEST OUTPUT:\n", state["tests"].test_output)
    print("\nTEST FAILURE REASON:\n", state["tests"].failure_reason)
    print("\nDEPLOYMENT:", state["deployment"].model_dump_json(indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI SDLC pipeline from the CLI.")
    parser.add_argument("--story", required=True, help="The raw user story / feature idea.")
    parser.add_argument("--language", default="python", help="Target programming language.")
    parser.add_argument("--open-pr", action="store_true", help="Attempt to open a real draft GitHub PR.")
    args = parser.parse_args()

    try:
        final = run_pipeline(args.story, args.language, args.open_pr)
        _print_result(final)
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)
