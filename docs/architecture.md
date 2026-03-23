# Syndical Core — Architecture

## 1. Overview

FastAPI-based campaign engine. Owns the full lifecycle: creation → content generation → human review → scheduling → publishing. All durable state lives in the pipeline model.

---

## 2. System Position

```
 [Client] ──► Syndical Core ──► [STIX/Visuals] (external)
                   │
                   └──► [LORE/Identity] (external)
```

| System | Owns                     |
|--------|--------------------------|
| Spark  | UI                       |
| STIX   | Visual / creative assets |
| LORE   | Identity / auth          |

---

## 3. Core Philosophy

- **Pipeline-first** — every campaign is a state machine; no action happens outside a defined stage.
- **Template-driven** — content rendered from versioned templates, not free-form input.
- **Human-in-the-loop** — explicit approve/reject required before publish.
- **Explicit over implicit** — nothing dispatches, schedules, or logs silently.

---

## 4. Core Modules

| Module                  | Responsibility                                                |
|-------------------------|---------------------------------------------------------------|
| Campaign Orchestrator   | Entry point; initialises and advances the pipeline            |
| Pipeline State Manager  | Validates and records state transitions                       |
| Content Generator       | Renders campaign content from versioned templates             |
| Human Review Handler    | Queues campaigns for approve/reject; attaches rejection reason|
| Scheduler               | Stores `run_at`; triggers publish at the appointed time       |
| Publisher               | Mock dispatch; logs publish event; swappable for real adapter |
| Logger                  | Append-only audit log: timestamp, campaign ID, actor, event   |

---

## 5. Pipeline States

```
CREATED → GENERATING_CONTENT → PENDING_REVIEW ──[reject]──► REJECTED
                                      │
                                 [approve]
                                      ▼
                              APPROVED → SCHEDULED → PUBLISHING → PUBLISHED
```

---

## 6. API Overview

Base path: `/api/v1`

| Method | Path                             | Action                  |
|--------|----------------------------------|-------------------------|
| POST   | `/campaigns`                     | Create campaign         |
| GET    | `/campaigns/{id}`                | Get state + details     |
| POST   | `/campaigns/{id}/generate`       | Trigger content gen     |
| POST   | `/campaigns/{id}/review/approve` | Approve                 |
| POST   | `/campaigns/{id}/review/reject`  | Reject                  |
| POST   | `/campaigns/{id}/schedule`       | Set `run_at`            |
| POST   | `/campaigns/{id}/publish`        | Dispatch immediately    |
| GET    | `/campaigns/{id}/logs`           | Fetch audit log         |

---

## 7. Data Flow

```
POST /campaigns              → CREATED
POST /{id}/generate          → GENERATING_CONTENT → PENDING_REVIEW
POST /{id}/review/approve    → APPROVED
POST /{id}/schedule          → SCHEDULED
[scheduler fires / manual]   → PUBLISHING → PUBLISHED
```

---

## 8. Non-Goals

- UI — **Spark**
- Visual assets — **STIX**
- Auth / identity — **LORE**
- Audience / contact data storage
- General-purpose message brokering

---

## 9. Future Evolution

| Capability                   | Notes                                          |
|------------------------------|------------------------------------------------|
| Real publisher adapters      | Email / SMS / social to replace mock           |
| Async pipeline               | Task queue (Celery / RQ) for long-running stages|
| Template management API      | CRUD endpoints for versioned templates         |
| Webhook notifications        | Emit state-change events to subscribers        |
| Publish retry policy         | Configurable retries on dispatch failure       |
| Multi-tenant isolation       | Campaign namespacing once LORE is integrated   |
