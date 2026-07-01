# AI-Driven SDLC Pipeline (Capstone Project)

An end-to-end, agentic SDLC pipeline that takes a plain-English user story and carries it through
**Requirement → Planning → Code Generation → Testing → Deployment (PR creation)**, fully automated
using LLM agents orchestrated with LangGraph, served via FastAPI, and powered by Claude through
the Portkey gateway.

This is a working vertical slice of a larger "AI-DLC Platform" concept — proving that an AI agent
chain can move a feature from idea to a tested, PR-ready code change with minimal human intervention.

---

## Architecture

```
                     ┌─────────────────────────────────────────────────────────┐
                     │                     ORCHESTRATOR (LangGraph)             │
                     │                                                         │
  User Story  ───▶   │  Requirement ──▶ Planning ──▶ Code ──▶ Test ──▶ Deploy   │  ──▶  Draft PR
  (any language)      │       Agent        Agent     Agent    Agent    Agent    │       + Report
                     │                                  ▲       │               │
                     │                                  └───────┘               │
                     │                              (retry loop on test fail,   │
                     │                               max 3 attempts)            │
                     └─────────────────────────────────────────────────────────┘
                                          │
                                          ▼
                              FastAPI backend (api/main.py)
                                          │
                                          ▼
                              Simple web UI (ui/index.html)
```

### Agents

| Agent | Input | Output |
|---|---|---|
| **Requirement Agent** | Raw user story text | Structured JSON: title, description, acceptance criteria, edge cases, priority, story points |
| **Planning Agent** | Requirement JSON | File/function breakdown, data model notes, architectural rationale |
| **Code Agent** | Planning JSON + target language | Generated source code + summary of assumptions |
| **Test Agent** | Code + acceptance criteria | Generated test code; executes Python tests in a sandbox and returns pass/fail. Non-Python languages get generated tests + static checks (execution sandbox is a documented extension point). |
| **Deployment Agent** | Passing code + tests | PR title/description/changelog, and (optionally) opens a real draft PR via GitHub API |

All agents communicate through strict JSON contracts (see `agents/schemas.py`), so any single agent
can be swapped or improved independently.

### Why Portkey

Claude calls go through [Portkey](https://portkey.ai) as a gateway, which gives this project for free:
- centralized API key management (no keys in code)
- request/response logging for every agent call (observability)
- automatic retries and fallback model routing
- per-run cost and token tracking

---

## Project structure

```
ai-sdlc-pipeline/
├── agents/
│   ├── schemas.py          # Pydantic models = the JSON contracts between agents
│   ├── prompts.py          # System prompts for each agent
│   ├── requirement_agent.py
│   ├── planning_agent.py
│   ├── code_agent.py
│   ├── test_agent.py
│   └── deployment_agent.py
├── orchestrator/
│   ├── graph.py            # LangGraph state machine wiring the 5 agents + retry loop
│   └── state.py            # Shared pipeline state object
├── sandbox/
│   └── runner.py           # Sandboxed execution of generated tests (Python via subprocess)
├── api/
│   └── main.py             # FastAPI app: POST /run, GET /run/{id}, GET /run/{id}/stream
├── ui/
│   └── index.html           # Single-page pipeline visualizer (vanilla JS, no build step)
├── storage/
│   └── db.py                # SQLite persistence for run history + metrics
├── portkey_client.py         # Thin wrapper around Portkey + Anthropic call
├── config.py                 # Env var loading
├── requirements.txt
├── .env.example
├── sample_runs/
│   └── example_story.txt
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
PORTKEY_API_KEY=your_portkey_api_key
PORTKEY_VIRTUAL_KEY=your_portkey_virtual_key_for_anthropic
ANTHROPIC_MODEL=claude-sonnet-4-6
GITHUB_TOKEN=your_github_pat_optional   # only needed for real PR creation
GITHUB_REPO=yourname/your-target-repo   # only needed for real PR creation
```

Get `PORTKEY_API_KEY` and `PORTKEY_VIRTUAL_KEY` from your Portkey dashboard (the virtual key wraps
your actual Anthropic key so it never lives in this codebase).

### 3. Run the backend

```bash
uvicorn api.main:app --reload --port 8000
```

### 4. Open the UI

Open `ui/index.html` directly in a browser (it talks to `http://localhost:8000`), or serve it:

```bash
python -m http.server 8080 --directory ui
```

Then visit `http://localhost:8080`.

### 5. Try it

Paste a user story, e.g.:

> "As a user, I want to reset my password via email so that I can regain access to my account if I forget it."

Pick a target language (Python / Java / TypeScript / etc.), click **Run Pipeline**, and watch each
of the five stages light up with its output.

---

## CLI usage (no UI needed)

```bash
python -m orchestrator.graph --story "As a user I want to..." --language python
```

Prints the full pipeline trace to stdout and saves a JSON run record to `storage/runs.db`.

---

## Production-readiness roadmap

This capstone intentionally ships a working vertical slice, not a finished product. Documented next
steps:

- [ ] Pydantic-strict schema validation with automatic re-prompt on malformed agent output
- [ ] Human-approval gate before Code and Deployment stages (currently fully autonomous)
- [ ] Multi-language sandboxed execution (currently Python-only execution; other languages get
      generated tests without auto-run — see `sandbox/runner.py` for the extension point)
- [ ] Real CI/CD trigger (GitHub Actions) instead of draft-PR-only deployment
- [ ] Secrets via a proper vault instead of `.env`
- [ ] Auth on the FastAPI endpoints
- [ ] Expand the pipeline to cover Design (wireframes) and Operations (incident response) stages

## License

MIT — built as an educational capstone project.
