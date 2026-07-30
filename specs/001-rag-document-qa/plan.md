# Implementation Plan: RAG Document Q&A Application

**Branch**: `001-rag-document-qa` | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-rag-document-qa/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A multi-user RAG application: users register/log in (email-or-username + password),
upload documents, and ask natural-language questions answered strictly from their own
uploaded content, with structured, schema-validated, cited responses saved to history.
Backend is FastAPI (Python) using Azure AI Search (Free tier, hybrid vector+keyword) for
retrieval and Azure OpenAI (`gpt-5.1`) for grounded generation with Pydantic-enforced
structured outputs (nested citations + token/context-window usage metadata), all Azure
calls authenticated via managed identity (no API keys). Frontend is React (TypeScript).
Metadata (users, documents, queries, answers, citations, comparison runs) persists in
SQLite via SQLAlchemy. An administrator/evaluator role (separate from regular users) runs
LangSmith-based experiments comparing two system versions against a benchmark dataset
using automated LLM-as-judge evaluators for correctness/relevance/groundedness, and views
Application Insights-backed operational metrics (latency, token consumption, error rate).

**This iteration's scope is local-only**: the application runs and is fully testable via
`uvicorn` against real Azure dependencies, authenticated with the developer's own
`az login` identity through the same `DefaultAzureCredential` code path that will later
pick up an App Service managed identity with zero application-code changes. It reuses
the existing Azure OpenAI resource (`aoai-jab4fcusuxtqs`, `gpt-5.1` deployment — not
provisioned by this project) and provisions one new Azure AI Search resource (Free tier)
plus the Key Vault and Application Insights resources the application depends on
regardless of hosting. Azure App Service and its Bicep module are explicitly deferred to
a future amendment; nothing below assumes App Service exists.

## Technical Context

**Language/Version**: Backend: Python 3.12. Frontend: TypeScript 5.x / Node 20 LTS.

**Primary Dependencies**: Backend — FastAPI, Pydantic v2, SQLAlchemy 2.x (async) +
`aiosqlite`, Alembic, `azure-identity` (`DefaultAzureCredential`), `openai` (Azure OpenAI
client, Structured Outputs), `azure-search-documents`, `bcrypt`, `pyjwt`, `langsmith`,
`azure-monitor-opentelemetry`. Frontend — React 18, Vite, React Router, a thin fetch/axios
API client.

**Storage**: SQLite (file-based, via SQLAlchemy + Alembic migrations) for relational
metadata — users, document metadata, queries, answers, citations, comparison-run
summaries, rate-limit counters. Document *content* (chunks + embeddings) lives in Azure
AI Search, not SQLite; raw uploaded bytes are processed in-memory during ingestion and
are not retained after indexing (see research.md).

**Testing**: Backend — pytest, pytest-asyncio, httpx (FastAPI `TestClient`/`ASGITransport`).
Frontend — Vitest + React Testing Library. Both cover success paths, failure paths, and
empty/malformed-input cases per constitution Principle III.

**Target Platform**: Local development machine running the FastAPI backend via
`uvicorn` and the React dev server (or its built static output served by FastAPI), for
this iteration. Azure App Service hosting is deferred — see Deployment Scope below —
and the codebase is structured so adding it later requires no application-logic changes
(only a new Bicep module and, eventually, a switched credential source that
`DefaultAzureCredential` already handles transparently).

**Project Type**: Web application (frontend + backend); single deployable unit once
hosting is added, run as two local processes for now.

**Performance Goals**: ≥95% of question-answer responses returned within 15 seconds
end-to-end (SC-011); admin metrics/comparison views reflect data no more than 5 minutes
stale (SC-009, SC-010).

**Constraints**: No hardcoded secrets/API keys anywhere; all Azure service calls use
managed identity (constitution Principle II) — for this iteration that means the
developer's own `az login` credential via `DefaultAzureCredential`, the constitution's
explicitly accepted local-development exception. Azure AI Search **Free tier**: 50 MB
storage and 3 indexes per service, no semantic ranker, no private endpoints/SLA — hybrid
(vector + keyword) search only, accepted as an explicit scope constraint. Per-user rate
limits: 50 uploads / 200 questions per rolling 24h (FR-012, default from spec
Assumptions). JWT (HS256) signing secret and the LangSmith API key are non-Azure
secrets and MUST be stored in Azure Key Vault, resolved at runtime via
`DefaultAzureCredential` (constitution Technology & Security Standards) — today via the
developer's own RBAC grant, later via an App Service managed identity, with no code
change either way.

**Deployment Scope (this iteration)**: Reuse the existing Azure OpenAI resource
`aoai-jab4fcusuxtqs` (`gpt-5.1` deployment) — no new Azure OpenAI resource is
provisioned. Provision exactly one new Azure AI Search resource (Free tier, zero cost,
no quota request needed) for this project. Do **not** provision Azure App Service or
any App Service Bicep module yet; that is explicitly out of scope until a future
amendment requests deployment.

**Scale/Scope**: Small-to-moderate multi-tenant deployment consistent with Azure AI
Search Free tier's storage ceiling; 5 user-facing capability areas (auth, upload/ask,
history, admin evaluation, admin ops metrics) per spec.md.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Code Quality | Ruff + Black (backend), ESLint + Prettier (frontend) enforced in CI; single-responsibility service modules (auth, retrieval, generation, rate-limit, eval, metrics) rather than one monolithic module. | PASS |
| II. Secure Credential Handling | Azure AI Search and Azure OpenAI calls authenticated via `DefaultAzureCredential` + RBAC role assignments (no keys). For this local-only iteration, `DefaultAzureCredential` resolves via the developer's `az login` session — exactly the constitution's named local-development exception, not a deviation from it. The two secrets with no managed-identity equivalent — JWT signing key and LangSmith API key — are stored in Azure Key Vault and resolved at runtime, never inlined or checked in. `.env.example` only, never a populated `.env`. | PASS |
| III. Automated Testing Discipline | Backend tests use pytest per the constitution's literal requirement. The React frontend cannot execute pytest (it isn't Python); it uses Vitest + React Testing Library as the JS-ecosystem equivalent, held to the same success/failure/empty/malformed-input coverage bar. This is a language-scope clarification of Principle III, not a reduction in its testing bar — flagged here per the compliance-review expectation in Governance. | PASS (clarified) |
| IV. CI Enforcement | CI pipeline (established during implementation) runs lint, format check, full pytest + Vitest suites, and secret scanning (e.g., gitleaks) on every PR; all four must pass before merge. | PASS |
| V. Incremental, Reviewable Delivery | Project structure and the upcoming `/speckit-tasks` breakdown are organized per user story (auth → core Q&A → history → eval comparison → ops metrics) so each stage ships as its own reviewable, working PR rather than one large change. | PASS |

No unjustified violations. The single noted item (testing-tool scope per language) is a
clarification, not a deviation, so the Complexity Tracking table below is intentionally
empty.

**Post-Phase-1 re-check**: research.md and data-model.md were reviewed against this
table after Phase 1 design. Adding Key Vault, Application Insights/Log Analytics, and
the mandatory user-scoped Azure AI Search filter did not introduce any new violation —
Key Vault/monitoring satisfy Principle II and FR-027/028 rather than working around
them, and the search filter is an implementation of FR-006, not a deviation from it. All
gates remain PASS.

**Amendment re-check (deployment scope narrowed to local-only)**: Deferring App
Service and reusing the existing Azure OpenAI resource does not introduce a new
violation — Principle II is satisfied either way because `DefaultAzureCredential` is
used unconditionally, and the constitution names the developer-CLI-login fallback as an
accepted local-development path explicitly. Key Vault and Application Insights are still
provisioned now (they don't require App Service to exist), so Principle II and
FR-027/028 remain satisfied rather than deferred. All gates remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-rag-document-qa/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                  # FastAPI routers
│   │   ├── auth.py           # register, login
│   │   ├── documents.py      # upload, list, delete
│   │   ├── queries.py        # ask question, list/get history
│   │   ├── admin_eval.py     # dataset items, comparison runs (admin/evaluator only)
│   │   └── admin_metrics.py  # operational health metrics (admin/evaluator only)
│   ├── models/
│   │   ├── db.py             # SQLAlchemy ORM models (User, Document, Query, Answer,
│   │   │                     #   Citation, ComparisonRun, RateLimitCounter)
│   │   └── schemas.py        # Pydantic request/response + structured-output models
│   │                         #   (Answer, Citation, ResponseMetadata)
│   ├── services/
│   │   ├── auth_service.py       # register/login, bcrypt hashing, JWT issue/verify
│   │   ├── document_service.py   # upload validation, parse/chunk, delete
│   │   ├── retrieval_service.py  # Azure AI Search hybrid query (user-scoped filter)
│   │   ├── generation_service.py # Azure OpenAI structured-output call
│   │   ├── rate_limit_service.py # per-user rolling-window counters
│   │   ├── eval_service.py       # LangSmith dataset + comparison-run orchestration
│   │   └── metrics_service.py    # Application Insights telemetry emission/query
│   ├── core/
│   │   ├── config.py         # settings (non-secret), Key Vault secret resolution
│   │   ├── security.py       # FastAPI dependency: current-user-from-JWT, role check
│   │   └── db.py             # async session/engine setup
│   └── main.py                # app factory, router registration, static frontend mount
├── alembic/                   # schema migrations
└── tests/
    ├── contract/               # per-endpoint request/response contract tests
    ├── integration/            # register→login→upload→ask→cite→history; admin eval; rate limits
    └── unit/                   # service-level unit tests (incl. empty/malformed inputs)

frontend/
├── src/
│   ├── components/            # DocumentUpload, ChatInput, AnswerCard, CitationList,
│   │                          #   HistoryList, LoginForm, RegisterForm, AdminDashboard
│   ├── pages/                 # Login, Register, Workspace, History, AdminEval, AdminMetrics
│   ├── services/               # api client (attaches JWT), auth context
│   └── main.tsx
└── tests/                      # Vitest + React Testing Library

eval/
├── dataset_sync.py            # pushes Evaluation Dataset Items into a LangSmith dataset
├── evaluators/                 # correctness.py, relevance.py, groundedness.py (LLM-as-judge)
└── run_experiment.py           # runs/compares two named app versions via LangSmith

infra/
├── main.bicep                  # orchestrates the modules below (no App Service module
│                               #   in this iteration — deferred to a future amendment)
├── main.parameters.json        # includes principalId (developer's az-login object id)
│                               #   and existingOpenAiName/existingOpenAiResourceGroup
└── modules/
    ├── search.bicep             # Azure AI Search (Free SKU) — the one new resource
    ├── keyvault.bicep           # Key Vault (JWT secret, LangSmith API key)
    ├── monitoring.bicep         # Application Insights + Log Analytics workspace
    └── roles.bicep              # RBAC role assignments (Search Index Data
                                  #   Contributor/Reader, Key Vault Secrets User on the
                                  #   new resources; Cognitive Services OpenAI User on
                                  #   the existing aoai-jab4fcusuxtqs resource) to the
                                  #   developer's principalId — swapped for an App
                                  #   Service managed identity's principalId once
                                  #   deployment is added, with no other change
```

Note: no `azure.yaml`/`azd` service definition yet — there is no hosted service to
target. `infra/main.bicep` is provisioned directly (`az deployment group create` or
`azd provision` in infra-only mode); `azd deploy`/`azure.yaml` are added together with
the App Service module in a future amendment.

**Structure Decision**: Web-application layout with two top-level app trees
(`backend/`, `frontend/`) plus `eval/` (LangSmith dataset/experiment tooling, decoupled
from the request-serving path) and `infra/` (Bicep). For this iteration, `backend/` and
`frontend/` run as two local processes (`uvicorn` + Vite dev server, or the built static
bundle served by FastAPI) rather than one App Service — matching the user's explicit
scope for this pass (reuse existing Azure OpenAI, add one new Azure AI Search resource,
no App Service yet). All application code (`core/config.py`, `retrieval_service.py`,
`generation_service.py`) is written against `DefaultAzureCredential` with no
environment-conditional branching, so introducing the App Service module later changes
only `infra/` and which principal holds the RBAC role assignments — never
`backend/src/`.

## Complexity Tracking

> No Constitution Check violations require justification; this table is intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
</content>
