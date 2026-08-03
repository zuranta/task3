# RAG Document Q&A Application

A multi-user application where each user uploads their own documents and asks
natural-language questions that are answered **only** from that content — every
answer is grounded, cited back to the source passage, structured (never free
text), and safe to revisit later exactly as it was first generated. The
system's own answer quality is measurable: an admin/evaluator role runs two
named versions of the app against a benchmark question set and gets an
automated, scored verdict on which one is more correct, relevant, and
grounded — plus live operational metrics (latency, tokens, error rate) for
production visibility.

## Table of contents

- [What this is](#what-this-is)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Testing](#testing)
- [Evaluation](#evaluation)
- [CI/CD](#cicd)
- [Infrastructure (Azure)](#infrastructure-azure)
- [Security](#security)
- [Current scope & limitations](#current-scope--limitations)
- [Documentation map](#documentation-map)

## What this is

The original brief: build a RAG (retrieval-augmented generation) app that
lets a user upload documents and ask questions about them, retrieving
relevant source material, generating a grounded answer with citations back to
the specific documents used, in a validated structured format (not free
text). Results are saved so a user can revisit past queries. Errors are
handled gracefully with clear, non-leaking messages. Separately, the system's
behavior must be *measurable*: what counts as a "correct," "relevant," and
"grounded" (non-hallucinated) answer is defined precisely, a benchmark
dataset of example questions/expected-answers is maintained, and two
versions of the system can be compared against it to determine which
performs better. Operational health (latency, token consumption, error
rate) is tracked in production. The system is multi-user: each account only
ever sees its own documents, queries, and results.

The full spec (user stories, functional requirements, edge cases, success
criteria) lives in [`specs/001-rag-document-qa/spec.md`](specs/001-rag-document-qa/spec.md).
It breaks down into six user stories:

| # | Story | Priority |
|---|---|---|
| 1 | Register and log in to a personal account (email-or-username + password) | P1 |
| 2 | Ask grounded, cited questions over your own uploaded documents | P1 |
| 3 | Revisit past queries and answers exactly as originally returned | P2 |
| 4 | (Admin) Compare two system versions against a benchmark dataset | P2 |
| 5 | (Admin) Monitor operational health (latency, tokens, error rate) | P3 |
| 6 | Experience a polished, conversational Q&A interface | P2 |

## How it works

```text
┌─────────────┐      ┌──────────────────┐      ┌────────────────────┐
│   Frontend   │─────▶│  FastAPI backend │─────▶│  Azure AI Search    │
│ React + Vite │  /api│  (Python 3.12)   │      │  (hybrid retrieval, │
│  (chat UI)   │◀─────│                  │      │   user-scoped)      │
└─────────────┘      └────────┬─────────┘      └────────────────────┘
                               │                ┌────────────────────┐
                               ├───────────────▶│  Azure OpenAI       │
                               │                │  (embeddings +      │
                               │                │   structured        │
                               │                │   generation)       │
                               │                └────────────────────┘
                               ├───────────────▶ SQLite (users, docs,
                               │                 queries, answers,
                               │                 citations, metadata)
                               ├───────────────▶ Azure Key Vault
                               │                 (JWT secret, LangSmith key)
                               └───────────────▶ Application Insights
                                                 (telemetry)

eval/ (LangSmith) ──runs the same retrieval+generation pipeline standalone──▶
                    against a benchmark dataset, scored by 3 LLM-as-judge
                    evaluators, decoupled from the request-serving path.
```

**Ask-a-question flow**: a question is embedded (Azure OpenAI), then Azure AI
Search runs a hybrid (vector + BM25 keyword) query scoped by a
server-injected `user_id` + `status=active` filter — never a client-suppliable
one, so cross-user data isolation is enforced at the retrieval layer itself,
not just the API layer. The retrieved passages are handed to Azure OpenAI's
Structured Outputs feature, constrained directly to a Pydantic `Answer` model
(`status`, `answer_text`, `citations[]`, token/context-window usage) — a
malformed response is a hard SDK-level error, never a parsing gamble, which is
what guarantees the "never free text" requirement. If the model can't ground
an answer in the retrieved passages, or fabricates a "grounded" answer with
zero citations, the system explicitly downgrades it to `no_answer_found`
rather than persist a hallucination. Each cited passage's exact text is
snapshotted onto its `Citation` row at answer time (not re-fetched later), so
revisiting a past answer — or clicking a citation to see what it was grounded
in — always shows exactly what was originally used, even if the source
document is later deleted or re-indexed.

**Document lifecycle**: an uploaded file (pdf/docx/txt/md, ≤10 MB) is parsed,
chunked, embedded, and upserted into Azure AI Search tagged
`status: active`; deleting a document flips it to `status: deleted` (removed
from future retrieval) while its `documents` row and any citations that
reference it are kept, so existing answers still resolve their source's
filename and correctly show it as removed.

**Chat interface**: the live Q&A screen holds its conversation as client-side
state only (`role`, `content`, `citations`, `timestamp`, `status`) — a
rendering projection of the same `Query`/`Answer`/`Citation` rows the backend
already persists, not a new entity. Submitting a question appends the user's
message and a pending assistant placeholder immediately, showing an animated
typing indicator until the backend responds (the backend returns one JSON
response, not a token stream, so this is not literal token-by-token
streaming), then updates that placeholder to the complete cited answer or a
styled error bubble.

## Tech stack

**Backend** — Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x (async) +
`aiosqlite` + Alembic, `azure-identity` (`DefaultAzureCredential` — no API
keys anywhere), `openai` (Azure OpenAI client, Structured Outputs),
`azure-search-documents`, `azure-keyvault-secrets`, `bcrypt`, `pyjwt`,
`langsmith`, `azure-monitor-opentelemetry`/`azure-monitor-query`, `pypdf` +
`python-docx` for document parsing.

**Frontend** — React 18 + TypeScript + Vite + React Router, Tailwind CSS +
hand-authored [shadcn/ui](https://ui.shadcn.com) primitives (button, input,
textarea, label, card, alert, badge, avatar, skeleton, separator, dialog,
table) as the single shared design system.

**Data & retrieval** — SQLite (relational metadata: users, documents,
queries, answers, citations, comparison runs, rate-limit counters) + Azure AI
Search (Free tier, hybrid vector+keyword retrieval — document *content*
itself, never SQLite) + Azure OpenAI (`gpt-5.1` deployment, reused from an
existing resource, not provisioned by this project).

**Evaluation** — LangSmith (dataset of record for benchmark
question/expected-answer pairs + experiment tracking), three custom
LLM-as-judge evaluators.

**Observability** — Application Insights + Log Analytics, OpenTelemetry
auto-instrumentation tagged by request stage (`upload`/`retrieval`/`generation`).

**Infra** — Bicep (`infra/`), provisioning Azure AI Search (Free SKU), Key
Vault, Application Insights/Log Analytics, and RBAC role assignments —
authenticated via the developer's own `az login` identity for this
iteration (see [Current scope & limitations](#current-scope--limitations)).

**Tooling** — Ruff + Black (backend), ESLint + Prettier (frontend), pytest +
pytest-asyncio + httpx (backend tests), Vitest + React Testing Library
(frontend tests), GitHub Actions CI, Gitleaks secret scanning.

## Project structure

```text
backend/    FastAPI app — api/ (routers), services/ (business logic),
            models/ (SQLAlchemy + Pydantic), core/ (config, security, db),
            alembic/ (migrations), tests/ (contract, integration, unit)
frontend/   React app, organized by feature (not technical layer) —
            features/{auth,upload,query,chat,history,admin}/, plus
            components/ui/ (the shared shadcn/ui primitives) and lib/
eval/       Standalone LangSmith dataset sync + comparison-run harness,
            decoupled from the request-serving path
infra/      Bicep: Azure AI Search, Key Vault, Application Insights,
            RBAC role assignments
specs/      spec-driven-development artifacts for this feature: spec.md,
            plan.md, research.md, data-model.md, contracts/openapi.yaml,
            quickstart.md, tasks.md
.github/    CI workflow (lint, format, test, secret scan on every PR)
Makefile    Local dev shortcuts (gitignored — this is a personal file per
            developer, see below)
```

See [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md) for stack-specific setup,
testing, and structure detail.

## Getting started

Prerequisites: Python 3.12, Node 20 LTS, an Azure subscription with
`az login` completed (so `DefaultAzureCredential` resolves your developer
identity — no API keys are used anywhere in this project).

```bash
# One-time: provision this project's Azure resources (Search, Key Vault,
# Application Insights — reuses an existing Azure OpenAI resource)
az login
az deployment group create \
  --resource-group <your-resource-group> \
  --template-file infra/main.bicep \
  --parameters principalId=$(az ad signed-in-user show --query id -o tsv)

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env   # fill in the endpoints/URIs the deployment above output
alembic upgrade head
uvicorn src.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Full step-by-step scenarios (register, upload, ask, revisit history, admin
eval/metrics, rate limiting) are in
[`specs/001-rag-document-qa/quickstart.md`](specs/001-rag-document-qa/quickstart.md).

## Testing

| Suite | Count | Command |
|---|---|---|
| Backend (pytest) — contract, integration, unit | 128 | `cd backend && pytest` |
| Frontend (Vitest + React Testing Library) | 36 | `cd frontend && npm run test` |
| Evaluation harness (pytest) | 8 | `pytest eval/tests` |

Every suite covers success paths, failure paths, and empty/malformed-input
cases — not just the happy path. Backend tests mock Azure AI Search and Azure
OpenAI at the service boundary (an in-memory fake index honoring the same
`user_id`+`status=active` filter the real service injects, so tests exercise
the actual cross-user isolation invariant, not just a mocked bypass);
`pytest` never makes a real network call. Frontend tests mock the service
layer (`src/features/*/*.ts`) rather than hitting a real backend.

Notable things specifically tested, beyond ordinary CRUD:

- Cross-user data isolation — every document/query read and write is scoped
  by the authenticated user's ID at the query level; the retrieval filter
  can't be overridden by malicious question content.
- The zero-citation groundedness guard — an "answered" result with no
  supporting passages is rejected/downgraded, never persisted as grounded.
- A passage cited twice by the model persists as exactly one citation, not a
  duplicate.
- Rate limiting (50 uploads / 200 questions per rolling 24h) returns a clear
  429 rather than silently processing over the limit.
- An unexpected exception's message never reaches the client (only curated,
  non-leaking error text) — a direct regression test for FR-021.
- Admin-only routes reject non-admin callers (403) across every eval/metrics
  endpoint.

## Evaluation

This is what makes "the answers are grounded and correct" a measurable claim
instead of an assertion. An admin/evaluator account maintains a benchmark
dataset of question/expected-answer pairs — **LangSmith is the system of
record for this dataset**, not duplicated in SQLite — and can run two named
system versions against it (`eval/run_experiment.py`, also reachable via the
admin UI's comparison-run feature).

Each dataset question is run through the same retrieval+generation pipeline
the live app uses (`eval/targets.py`), and the result is scored by three
independent LLM-as-judge evaluators (`eval/evaluators/`):

- **Correctness** — does the candidate answer factually match the reference
  answer (allowing for wording differences)?
- **Relevance** — does the answer address what was actually asked, regardless
  of whether it's correct?
- **Groundedness** — a citation-coverage check first (zero citations = never
  grounded; no answer claimed = trivially grounded), then an LLM-as-judge
  fallback verifying every claim is actually supported by the cited passages,
  allowing for paraphrasing.

A version's aggregate score is the mean of each evaluator's score across the
whole dataset; the version with the higher combined total wins (`tie` if
equal). A question a version fails to answer is recorded as a failure for
that version (LangSmith's `run.error`) — **never silently omitted** from the
comparison, so a version can't win by quietly skipping hard questions.
`ComparisonRun` summaries (winner, aggregate scores, LangSmith experiment
IDs) persist in SQLite so the admin UI can list past runs without querying
LangSmith directly each time; full per-question detail stays in LangSmith.

```bash
cd eval
python -m eval.dataset_sync           # sync admin-curated items into the LangSmith dataset
python -m eval.run_experiment --version-a "prompt-v1" --version-b "prompt-v2"
```

## CI/CD

Every pull request against `main` runs three required checks
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) — none can be
skipped or overridden:

1. **Backend** — Ruff lint, Black format check, full pytest suite.
2. **Frontend** — ESLint, Prettier format check, full Vitest suite.
3. **Secret scanning** — Gitleaks over the full history of the PR's commits.

## Infrastructure (Azure)

This iteration is **local-only**: the app runs via `uvicorn`/Vite against
real Azure dependencies, authenticated with the developer's own `az login`
identity through the same `DefaultAzureCredential` code path that will later
pick up an Azure App Service managed identity with zero application-code
changes. `infra/main.bicep` provisions exactly what this iteration needs and
nothing more:

- **Azure AI Search** (Free tier) — the one new resource this project
  provisions for hybrid retrieval.
- **Key Vault** — holds the JWT signing secret (auto-generated at deploy
  time) and the LangSmith API key (no managed-identity equivalent exists for
  it, so it's set once manually after deployment).
- **Application Insights + Log Analytics** — operational telemetry.
- **RBAC role assignments** — Search Index Data Contributor/Reader, Key Vault
  Secrets User on the new resources, and Cognitive Services OpenAI User on
  the **existing**, reused Azure OpenAI resource (in its own resource group,
  handled via a separately-scoped module) — all granted to the developer's
  `az login` principal for now.

No Azure App Service (or any hosting) is provisioned yet — see
[`specs/001-rag-document-qa/plan.md`](specs/001-rag-document-qa/plan.md)'s
Deployment Scope for what that future amendment changes (only `infra/` and
which principal holds the RBAC assignments — never application code, since
every credential already goes through `DefaultAzureCredential` unconditionally).

## Security

- **No hardcoded secrets anywhere.** Every Azure call authenticates via
  `DefaultAzureCredential` (RBAC role assignments, not keys). The two
  secrets with no managed-identity equivalent — the JWT signing key and the
  LangSmith API key — live in Key Vault, resolved at runtime, never inlined
  or checked in. Only `.env.example` is committed, never a populated `.env`.
- **Passwords** are hashed with bcrypt (cost 12); login failures (wrong
  password or unrecognized identifier) return one generic message, never
  revealing which field was wrong (prevents account enumeration).
- **Errors never leak internals** — every failure path returns a curated,
  static, non-leaking message (no stack traces, credentials, hostnames, or
  raw third-party payloads), enforced by a regression test and audited
  across every `raise` site in the backend.
- **Gitleaks** scans every PR's full commit history for accidentally
  committed secrets.

## Current scope & limitations

- **Local-only iteration**: no Azure App Service or other hosting is
  deployed; both apps run as two local processes against real (or, in
  tests, mocked) Azure dependencies.
- **No token-level streaming**: `POST /queries` returns one JSON response,
  not a chunked/SSE stream — the chat UI's typing indicator covers the full
  wait instead of revealing partial tokens.
- **No raw file storage**: original uploaded bytes are processed in-memory
  during ingestion and never retained — only the extracted, chunked passage
  text (in Azure AI Search) and metadata (in SQLite) persist. "Viewing a
  source" means viewing the indexed passage text, not the original PDF/docx.
- **Azure AI Search Free tier**: 50 MB storage, 3 indexes per service, no
  semantic ranker — a known, accepted scope constraint, not a bug.
- **Search-index propagation lag**: a question asked immediately after a
  document reaches `status: ready` can occasionally miss content that
  becomes searchable moments later (Azure AI Search indexing is near-real-time,
  not synchronous) — a retry a few seconds later succeeds; not currently
  mitigated in code.

## Documentation map

| Document | What's in it |
|---|---|
| [`specs/001-rag-document-qa/spec.md`](specs/001-rag-document-qa/spec.md) | User stories, functional requirements, edge cases, success criteria |
| [`specs/001-rag-document-qa/plan.md`](specs/001-rag-document-qa/plan.md) | Architecture, tech stack rationale, constitution compliance |
| [`specs/001-rag-document-qa/research.md`](specs/001-rag-document-qa/research.md) | Every major technical decision and why it was made |
| [`specs/001-rag-document-qa/data-model.md`](specs/001-rag-document-qa/data-model.md) | Entity definitions, storage location, validation rules, state transitions |
| [`specs/001-rag-document-qa/contracts/openapi.yaml`](specs/001-rag-document-qa/contracts/openapi.yaml) | The full API contract |
| [`specs/001-rag-document-qa/quickstart.md`](specs/001-rag-document-qa/quickstart.md) | Step-by-step manual validation scenarios |
| [`specs/001-rag-document-qa/tasks.md`](specs/001-rag-document-qa/tasks.md) | The full task breakdown this was built from |
| [`backend/README.md`](backend/README.md) | Backend-specific setup, testing, known limitations |
| [`frontend/README.md`](frontend/README.md) | Frontend-specific setup, design system, structure, routes |
| [`.specify/memory/constitution.md`](.specify/memory/constitution.md) | The project's non-negotiable engineering principles |

This project was built using a spec-driven development workflow (spec →
plan → tasks → implement, under `specs/001-rag-document-qa/`), with each
user story delivered as its own reviewable, independently-tested increment.
