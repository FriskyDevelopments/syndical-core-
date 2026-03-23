# Syndical Core — Architecture

## 1. Overview

Syndical Core is a FastAPI-based backend service that acts as the central campaign engine for the Syndical platform. It orchestrates the full lifecycle of a campaign: from creation and content generation through human review, scheduling, and publishing.

It is designed to be stateless at the request layer, with all durable state managed through a well-defined pipeline model.

---

## 2. System Position

Syndical Core sits at the center of the Syndical backend ecosystem. It receives campaign instructions, drives them through the pipeline, and emits results. It does **not** own the UI, visual rendering, or identity concerns — those are delegated to separate services.

```
          ┌────────────────────────────────────────────┐
          │               Syndical Core                │
          │                                            │
 [Client] ──► [API Layer]  ──►  [Pipeline Engine]     │
          │        │                    │              │
          │   [Scheduling]    [Content Generation]     │
          │        │                    │              │
          │   [Publisher]     [Human Review Queue]     │
          │        │                    │              │
          │     [Logger]      [State Manager]          │
          └────────────────────────────────────────────┘
                    │                    │
               [STIX/Visuals]        [LORE/Identity]
               (external)            (external)
```

**Adjacent systems (not owned by Syndical Core):**

| System | Responsibility           |
|--------|--------------------------|
| Spark  | UI / front-end           |
| STIX   | Visual / creative assets |
| LORE   | Identity / auth logic    |

---

## 3. Core Philosophy

- **Pipeline-first**: every campaign is a state machine. No campaign action happens outside of a defined pipeline stage.
- **Template-driven content**: content is generated from structured templates, not free-form input, ensuring consistency and auditability.
- **Human-in-the-loop**: campaigns require an explicit approve/reject step before any publishing occurs.
- **Explicit over implicit**: scheduling, publishing, and logging are all deliberate, logged actions — nothing happens silently.
- **Separation of concerns**: Syndical Core does one thing (campaign orchestration) and delegates everything else.

---

## 4. Core Modules

### 4.1 Campaign Orchestrator
The top-level coordinator. Accepts campaign definitions, initialises the pipeline, and routes the campaign through each stage in sequence.

### 4.2 Pipeline State Manager
Maintains the current state of every campaign in the system. Transitions are validated against the allowed state graph; invalid transitions are rejected with a descriptive error.

### 4.3 Content Generator
Produces campaign content by rendering parameterised templates. Templates are versioned and stored separately from runtime state.

### 4.4 Human Review Handler
Places a campaign in a review queue after content generation. Exposes endpoints for reviewers to approve or reject. Rejection returns the campaign to a configurable earlier stage with a reason attached.

### 4.5 Scheduler
Assigns an execution time to an approved campaign. Supports immediate dispatch and future-dated scheduling. Persists schedule metadata alongside campaign state.

### 4.6 Publisher
Executes the final dispatch of a campaign. Currently implemented as a mock that logs the publish event and marks the campaign as published. Designed for straightforward replacement with real delivery integrations.

### 4.7 Logger
Provides structured, append-only audit logging for every state transition and system event. All log entries include a timestamp, campaign ID, actor, and event type.

---

## 5. Pipeline States

A campaign moves through the following states in order. Each arrow represents a valid transition.

```
CREATED
   │
   ▼
GENERATING_CONTENT
   │
   ▼
PENDING_REVIEW
   │
   ├──[reject]──► REJECTED
   │
   ▼  [approve]
APPROVED
   │
   ▼
SCHEDULED
   │
   ▼
PUBLISHING
   │
   ▼
PUBLISHED
```

| State               | Description                                              |
|---------------------|----------------------------------------------------------|
| `CREATED`           | Campaign record initialised; no content yet              |
| `GENERATING_CONTENT`| Content generator is rendering templates                 |
| `PENDING_REVIEW`    | Awaiting human approve/reject action                     |
| `APPROVED`          | Reviewer has approved content                            |
| `REJECTED`          | Reviewer has rejected content; campaign is terminal      |
| `SCHEDULED`         | Approved campaign has a confirmed execution time         |
| `PUBLISHING`        | Publisher is executing the dispatch                      |
| `PUBLISHED`         | Campaign has been successfully dispatched                |

---

## 6. API Overview

All endpoints are prefixed with `/api/v1`.

| Method | Path                                      | Description                              |
|--------|-------------------------------------------|------------------------------------------|
| POST   | `/campaigns`                              | Create a new campaign                    |
| GET    | `/campaigns/{id}`                         | Retrieve campaign details and state      |
| POST   | `/campaigns/{id}/generate`                | Trigger content generation               |
| POST   | `/campaigns/{id}/review/approve`          | Approve a campaign in review             |
| POST   | `/campaigns/{id}/review/reject`           | Reject a campaign in review              |
| POST   | `/campaigns/{id}/schedule`                | Schedule an approved campaign            |
| POST   | `/campaigns/{id}/publish`                 | Trigger immediate publish (if scheduled) |
| GET    | `/campaigns/{id}/logs`                    | Retrieve audit log for a campaign        |

All requests and responses use JSON. Errors follow a standard envelope:

```json
{
  "error": "INVALID_STATE_TRANSITION",
  "detail": "Cannot approve a campaign in state CREATED."
}
```

---

## 7. Data Flow

### Happy path: campaign creation to publish

```
1. Client POSTs /campaigns
       → Orchestrator creates campaign record (state: CREATED)
       → Logger records CAMPAIGN_CREATED event

2. Client POSTs /campaigns/{id}/generate
       → State transitions to GENERATING_CONTENT
       → Content Generator renders template
       → State transitions to PENDING_REVIEW
       → Logger records CONTENT_GENERATED event

3. Reviewer POSTs /campaigns/{id}/review/approve
       → State transitions to APPROVED
       → Logger records CAMPAIGN_APPROVED event

4. Client POSTs /campaigns/{id}/schedule  { "run_at": "2026-04-01T09:00:00Z" }
       → State transitions to SCHEDULED
       → Scheduler persists run_at
       → Logger records CAMPAIGN_SCHEDULED event

5. Scheduler fires at run_at (or client triggers manually)
       → State transitions to PUBLISHING
       → Publisher executes dispatch (mock: logs intent)
       → State transitions to PUBLISHED
       → Logger records CAMPAIGN_PUBLISHED event
```

---

## 8. Non-Goals

Syndical Core explicitly does **not**:

- Render UI or serve front-end assets (owned by **Spark**)
- Generate or store visual/creative assets (owned by **STIX**)
- Handle user authentication, authorisation, or identity management (owned by **LORE**)
- Store raw audience or contact data
- Act as a general-purpose messaging broker

---

## 9. Future Evolution

| Capability                        | Notes                                                         |
|-----------------------------------|---------------------------------------------------------------|
| Real publisher integrations       | Replace mock publisher with email/SMS/social adapters         |
| Async pipeline execution          | Move long-running stages to a task queue (e.g. Celery/RQ)     |
| Template versioning API           | Expose CRUD endpoints for template management                 |
| Webhook notifications             | Emit events on state transitions for external subscribers     |
| Retry logic for failed publishes  | Add configurable retry policy to the publishing stage         |
| Multi-tenant campaign isolation   | Namespace campaigns by organisation once LORE integration matures |
