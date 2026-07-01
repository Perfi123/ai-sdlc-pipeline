"""
FastAPI backend exposing the AI SDLC pipeline.

Endpoints:
  POST /run            -> kick off a pipeline run (synchronous, returns full result)
  GET  /runs            -> list past runs (for the report/history view)
  GET  /run/{run_id}     -> get a specific past run's stored result

Run with: uvicorn api.main:app --reload --port 8000
"""
import time
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator.graph import run_pipeline
from storage.db import init_db, create_run, complete_run, get_run, list_runs

app = FastAPI(title="AI SDLC Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo/capstone setting; restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


class RunRequest(BaseModel):
    user_story: str
    language: str = "python"
    open_real_pr: bool = False


@app.post("/run")
def run(req: RunRequest):
    if not req.user_story or len(req.user_story.strip()) < 10:
        raise HTTPException(status_code=400, detail="user_story is required and should be a real sentence.")

    run_id = create_run(req.user_story, req.language)
    start = time.time()

    try:
        final_state = run_pipeline(req.user_story, req.language, req.open_real_pr)
        elapsed = round(time.time() - start, 2)

        result = {
            "run_id": run_id,
            "elapsed_seconds": elapsed,
            "status_log": final_state["status_log"],
            "requirement": final_state["requirement"].model_dump(),
            "plan": final_state["plan"].model_dump(),
            "code": final_state["code"].model_dump(),
            "tests": final_state["tests"].model_dump(),
            "deployment": final_state["deployment"].model_dump(),
            "retry_count": final_state.get("retry_count", 0),
        }

        status = "success"
        if final_state["tests"].executed and not final_state["tests"].passed:
            status = "completed_with_failing_tests"

        complete_run(run_id, status, result)
        result["status"] = status
        return result

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        error_result = {
            "run_id": run_id,
            "elapsed_seconds": elapsed,
            "error": str(e),
            "trace": traceback.format_exc(),
        }
        complete_run(run_id, "failed", error_result)
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")


@app.get("/runs")
def runs(limit: int = 50):
    return list_runs(limit)


@app.get("/run/{run_id}")
def run_detail(run_id: str):
    run_row = get_run(run_id)
    if not run_row:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run_row


@app.get("/health")
def health():
    return {"status": "ok"}
