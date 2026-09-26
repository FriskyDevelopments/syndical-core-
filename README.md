# Syndical Core

**FastAPI campaign engine — the campaign lifecycle as an explicit state machine**

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)

The core of Syndical, a campaign-management backend. The current code is a small **FastAPI** service (`main.py`) that creates campaigns (name and "aura"), lists them and moves each one through an explicit status pipeline: `idea → drafted → designed → reviewed → approved → scheduled → published → archived`. State is kept **in memory** for now. The target design is in [`docs/architecture.md`](docs/architecture.md): template-driven content generation, a human-in-the-loop review, scheduling, a swappable publisher and an append-only audit log, with UI, visuals and identity owned by the sibling systems Spark, STIX and LORE. It's for developers building the Syndical campaign pipeline.

## Architecture

```mermaid
flowchart LR
  client([Client · Spark UI]) -->|REST| api[FastAPI app<br/>main.py]
  api --> store[(In-memory store<br/>campaigns dict)]
  api -.->|planned| stix[STIX · visual assets]
  api -.->|planned| lore[LORE · identity / auth]
```

### Campaign status pipeline (as implemented)

```mermaid
stateDiagram-v2
  [*] --> idea: POST /campaigns
  idea --> drafted
  drafted --> designed
  designed --> reviewed
  reviewed --> approved
  approved --> scheduled
  scheduled --> published
  published --> archived
  note right of idea: PATCH /campaigns/{id}/state sets any status (transitions aren't enforced yet)
```

## Stack

- Python, FastAPI, Pydantic v2
- Uvicorn (ASGI server)

## Project structure

```text
main.py               FastAPI app: models + endpoints (in-memory)
requirements.txt      fastapi, uvicorn[standard], pydantic
docs/architecture.md  target architecture, pipeline states, planned /api/v1 surface
```

## Deploy

There's no deploy configuration in the repository yet. Run it with any ASGI host, e.g. `uvicorn main:app`. Data doesn't persist across restarts.
