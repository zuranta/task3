# Phase 0 Research: RAG Document Q&A Application

All major technology choices were specified directly by the user, so this research
focuses on resolving the *implementation-level* unknowns those choices leave open —
integration patterns, security-critical defaults, and the couple of gaps (raw-file
retention, rate-limit storage, secrets home) the spec/user input didn't pin down.

## 1. Backend framework & structure

- **Decision**: FastAPI on Python 3.12, organized as `api/` (routers) → `services/`
  (business logic) → `models/` (SQLAlchemy + Pydantic) → `core/` (config, security, db).
- **Rationale**: User-specified. Layered structure keeps each service single-responsibility
  (constitution Principle I) and testable in isolation (unit tests mock the layer below).
- **Alternatives considered**: Flask/Django — rejected, not requested and FastAPI's native
  Pydantic integration is exactly what the structured-output requirement needs.

## 2. Frontend

- **Decision**: React 18 + TypeScript, built with Vite, served as static assets by the
  FastAPI backend in production (single deployable App Service).
- **Rationale**: User-specified React; Vite build output is a static bundle with no
  separate hosting requirement, which lets the whole app stay on the one App Service the
  user's infra list implies (no separate Static Web App resource was requested).
- **Alternatives considered**: Separate Azure Static Web App for the frontend — would work
  but adds a resource beyond what was specified and a second CORS-aware deployment unit
  for no functional benefit at this scale.

## 3. Retrieval: Azure AI Search (Free tier, hybrid)

- **Decision**: One Azure AI Search index (Free SKU) per deployment (not per user).
  Every document's fields include a `user_id` (filterable) and `status` (filterable,
  `active`/`deleted`). Every query — with no exception — includes a server-side-injected
  OData filter `user_id eq '{current_user_id}' and status eq 'active'`, never a
  client-supplied one. Hybrid search combines vector similarity (embedding field) with
  BM25 keyword search in a single query (Azure AI Search's native hybrid mode).
  Authentication uses Azure RBAC data-plane auth (`Search Index Data Contributor` for the
  ingestion path, `Search Index Data Reader` for the query path) via
  `DefaultAzureCredential` — no admin/query API keys.
- **Rationale**: A single shared index with a mandatory user-scoped filter is the standard
  Free-tier pattern (Free tier caps out at 3 indexes total, ruling out one-index-per-user).
  The filter is the sole enforcement point for FR-006/SC-007 (cross-user data isolation)
  at the retrieval layer, so it must be applied in `retrieval_service.py` itself, not left
  to callers — this is a security-critical invariant, not a convenience default.
- **Alternatives considered**: One index per user — rejected, exceeds Free tier's 3-index
  cap almost immediately. Filtering only in the application layer after an unfiltered
  search — rejected, it would return other users' passages to the ranker/LLM before
  ever being filtered out, leaking content into the generation context.
- **Known constraint accepted**: Free tier has a 50 MB total storage ceiling and no
  semantic ranker; this bounds total indexed content across all users and rules out
  semantic re-ranking. Accepted per explicit user instruction; flagged as a scale risk
  the team should revisit if usage grows.

## 4. Generation: Azure OpenAI (`gpt-5.1`) with structured outputs

- **Decision**: Azure OpenAI Python SDK client authenticated via
  `DefaultAzureCredential` + Entra ID token (`Cognitive Services OpenAI User` role),
  targeting the **existing** `aoai-jab4fcusuxtqs` resource's `gpt-5.1` deployment — this
  project provisions no Azure OpenAI resource of its own, only a role assignment
  granting the current principal data-plane access to that existing resource.
  Responses are constrained using the SDK's Structured Outputs feature
  (JSON-schema-constrained decoding) bound directly to a Pydantic `Answer` model (nested
  `citations: list[Citation]` and `metadata: ResponseMetadata` with
  `prompt_tokens`/`completion_tokens`/`total_tokens`/`context_window_utilization`).
  `context_window_utilization` is computed as `total_tokens / model_context_window`
  using a configured constant for the deployment.
- **Rationale**: Matches the user's explicit instruction to reuse the existing resource
  rather than provision a duplicate (avoids redundant cost/quota use). Structured
  Outputs (rather than prompt-engineered JSON) is what guarantees FR-016 (validated
  structured format, never free text) at the API-contract level — a malformed response
  is a hard SDK-level error, not a parsing gamble.
- **Alternatives considered**: Provisioning a new, project-dedicated Azure OpenAI
  resource — rejected per explicit user instruction to reuse the existing one. Function/
  tool-calling to shape output — rejected, strict Structured Outputs is simpler and
  purpose-built for exactly this case.
- **Open item**: The existing resource's resource group is assumed to be usable as the
  deployment target for this project's other resources (Search, Key Vault, Monitoring),
  avoiding cross-resource-group Bicep scoping. If it lives in a different resource group
  than this project should deploy into, `main.bicep` takes an
  `existingOpenAiResourceGroup` parameter so `roles.bicep` can scope the role assignment
  correctly either way.

## 5. Persistence: SQLite via SQLAlchemy

- **Decision**: Async SQLAlchemy 2.x + `aiosqlite`, schema versioned with Alembic. Stores
  `User`, `Document` (metadata only), `Query`, `Answer`, `Citation`, `ComparisonRun`
  (summary), `RateLimitCounter`. Raw uploaded file bytes are parsed/chunked/embedded
  in-memory during ingestion and are **not** retained after indexing — only the resulting
  passages (in Azure AI Search) and metadata (in SQLite) persist.
- **Rationale**: User specified SQLite as acceptable for this scope. Not retaining raw
  bytes avoids requiring a blob-storage resource the user didn't list, since no
  requirement asks for original-file re-download — only for asking questions and citing
  extracted passages.
- **Alternatives considered**: Persisting raw files to local App Service disk — rejected,
  App Service's local filesystem isn't guaranteed durable/shared across
  restarts or scale-out instances, and nothing in the spec requires it.

## 6. Authentication & authorization

- **Decision**: Passwords hashed with `bcrypt` (cost factor 12) — direct `bcrypt` package,
  never logged or stored in plain text. Login accepts either `email` or `username` by
  querying `WHERE email = :id OR username = :id`. On success, issue a JWT (HS256) with a
  short expiry (e.g., 1 hour) containing `sub` (user id) and `role`; the signing secret is
  stored in Azure Key Vault and loaded once at app startup via managed identity — never an
  App Service plaintext setting. A FastAPI dependency (`get_current_user`) decodes/verifies
  the bearer token on every protected route; a second dependency (`require_admin`) layers
  role enforcement for the eval/metrics routes (FR-007).
- **Rationale**: Directly matches user-specified requirements (bcrypt, JWT HS256,
  email-or-username login, per-route validation) and constitution Principle II (JWT secret
  as a non-Azure credential must live in Key Vault).
- **Failure handling**: Login failures (wrong password OR unrecognized identifier) return
  one generic `401` message ("invalid credentials") to prevent user enumeration (FR-004).
  Registration conflicts return a `409` naming which field (email/username) collided,
  without exposing any other account's data (FR-003) — enforced via a unique constraint
  on both columns at the database level, not just an application-level check, so races
  can't create duplicates.

## 7. Data isolation enforcement

- **Decision**: Every data-access function in `services/` that touches Document, Query,
  Answer, or Citation rows requires the authenticated `user_id` as a parameter and applies
  it as a `WHERE` clause at the ORM query level (never fetch-then-filter-in-Python, never
  rely solely on the API layer or the UI hiding other users' data).
- **Rationale**: FR-006/SC-007 require 0% cross-user access; enforcing at the query layer
  means even a future new endpoint can't accidentally leak data by forgetting a UI-level
  check.

## 8. Rate limiting (FR-012)

- **Decision**: A `RateLimitCounter` SQLite table (`user_id`, `counter_type`,
  `window_start`, `count`), checked and incremented atomically within the same
  transaction as the upload/question request. Default limits: 50 uploads/24h, 200
  questions/24h (from spec Assumptions), returned as configuration values (not hardcoded
  magic numbers) so they can be tuned without a code change.
- **Rationale**: Single-instance, low-scale deployment (Free-tier-bounded) doesn't need a
  distributed limiter (e.g., Redis); a DB-backed rolling counter is sufficient and avoids
  introducing a new infrastructure dependency.
- **Alternatives considered**: In-memory counter — rejected, would reset on every App
  Service restart/redeploy and wouldn't survive multi-instance scale-out.

## 9. Evaluation: LangSmith

- **Decision**: Evaluation Dataset Items (FR-023) are the system of record in a LangSmith
  dataset (not duplicated in SQLite); a small `dataset_sync.py` script pushes
  admin-curated question/expected-answer pairs into it. Three custom evaluators
  (`correctness.py`, `relevance.py`, `groundedness.py`) implement FR-022's definitions,
  using LLM-as-judge calls to the same Azure OpenAI deployment for correctness/relevance,
  and a groundedness check that verifies each claim in the answer is attributable to a
  retrieved passage (citation-coverage check, cross-referenced with an LLM-as-judge
  fallback for paraphrased claims). `run_experiment.py` uses LangSmith's `evaluate()` API
  to run two named configurations (e.g., two prompt versions or two retrieval configs)
  against the dataset, producing per-question and aggregate scores; `ComparisonRun` rows
  in SQLite store just the summary (winner, aggregate scores, LangSmith experiment IDs)
  so the admin UI can list past runs without querying LangSmith directly each time.
- **Rationale**: Matches the user's explicit instruction; keeping full per-question detail
  in LangSmith (rather than re-storing it) avoids duplicating a system that already
  persists it durably.

## 10. Observability: Application Insights

- **Decision**: `azure-monitor-opentelemetry` auto-instruments FastAPI (request spans) and
  outbound calls (Azure AI Search, Azure OpenAI). Custom spans/attributes tag each request
  with its stage (`upload`/`retrieval`/`generation`) and, for generation calls, token
  counts as custom metric dimensions. Error rate and latency percentiles are derived from
  standard Application Insights `requests`/`dependencies` telemetry, queryable by stage
  and time window (FR-027/028, SC-009/SC-010) — no separate metrics table in SQLite.
- **Rationale**: "Application Insights or equivalent" was explicitly requested; the
  OpenTelemetry distro is the current first-party integration path for Python on Azure
  and needs no additional infrastructure beyond the Application Insights resource itself.

## 11. Infrastructure as code (revised: local-only iteration)

- **Decision**: Plain Bicep, deployed directly (`az deployment group create` or `azd
  provision` in infra-only mode — no `azure.yaml`/`azd deploy` yet, since there is no
  hosted service to target). Modules: `search.bicep` (the one new resource — Azure AI
  Search, Free SKU), `keyvault.bicep` (RBAC-mode Key Vault holding the JWT secret and
  LangSmith API key), `monitoring.bicep` (Application Insights + Log Analytics
  workspace), `roles.bicep` (role assignments — Search Index Data Contributor/Reader and
  Key Vault Secrets User on the new resources, Cognitive Services OpenAI User on the
  *existing* `aoai-jab4fcusuxtqs` resource — all scoped to a `principalId` parameter set
  to the developer's own `az login` object ID for this iteration). **No
  `appservice.bicep` and no new `openai.bicep`** — App Service is deferred to a future
  amendment, and Azure OpenAI is reused, not provisioned.
- **Rationale**: Directly implements this amendment's explicit scope: reuse the existing
  Azure OpenAI resource, add exactly one new Azure AI Search (Free tier, zero cost, no
  quota needed) resource, and skip App Service until deployment is actually requested.
  Key Vault and Application Insights are provisioned now regardless of hosting, because
  the application depends on them (secrets, FR-027/028 telemetry) whether it runs
  locally or on App Service later — deferring them would mean re-deriving this decision
  when App Service is eventually added, for no benefit.
- **Forward compatibility**: Every module and every application-code credential call
  uses `DefaultAzureCredential`, which resolves to the caller's `az login` identity today
  and will resolve to an App Service system-assigned identity automatically once that
  module is added — the only future change is a new `appservice.bicep` module plus
  re-pointing `roles.bicep`'s `principalId` parameter at the new managed identity's
  object ID. No line of `backend/src/` changes.
- **Alternatives considered**: Provisioning App Service now with the app simply not
  deployed to it yet — rejected, adds a real-cost resource and deployment-pipeline work
  the user explicitly said to skip for this iteration. App Service configuration-only
  secrets (no Key Vault) — rejected outright by constitution Principle II/Technology &
  Security Standards, independent of hosting choice.

## 12. CI enforcement

- **Decision**: GitHub Actions (or equivalent) pipeline running, per PR: `ruff` + `black
  --check` + `pytest` (backend), `eslint` + `prettier --check` + `vitest` (frontend), and
  a secret-scanning step (e.g., `gitleaks`). All four must pass before merge; no override.
- **Rationale**: Directly operationalizes constitution Principle IV.

**Output**: All open implementation questions above are resolved; no
`NEEDS CLARIFICATION` markers remain in the Technical Context.
</content>
