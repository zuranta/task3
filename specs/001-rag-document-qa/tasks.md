---

description: "Task list template for feature implementation"
---

# Tasks: RAG Document Q&A Application

**Input**: Design documents from `/specs/001-rag-document-qa/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Included as mandatory — constitution Principle III requires every feature/bug
fix to be covered by automated tests (pytest for the backend, Vitest + React Testing
Library for the frontend per plan.md's Constitution Check), covering success paths,
failure paths, and empty/malformed-input cases.

**Organization**: Tasks are grouped by user story (from spec.md, in priority order) to
enable independent implementation, testing, and delivery of each story.

**Regenerated**: This revision reflects the amended plan.md scope — reuse the existing
Azure OpenAI resource (`aoai-jab4fcusuxtqs`), provision exactly one new Azure AI Search
(Free tier) resource, defer Azure App Service, and run/test locally via `uvicorn` with
`DefaultAzureCredential` resolved through `az login`. It also folds in five gaps
surfaced by `/speckit-analyze` on the prior task list (Key Vault secret population, the
`POST /queries` failure-path test, the zero-citation groundedness guard, user-scoped
data-isolation unit tests beyond retrieval, and administrator-account provisioning) —
each is marked below with the finding ID it addresses.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in every description

## Path Conventions

Web application layout per plan.md: `backend/src/`, `backend/tests/`, `frontend/src/`,
`frontend/tests/`, `eval/`, `infra/`. No `azure.yaml`/`azd` service wiring yet — there is
no hosted service in this iteration.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository scaffolding, tooling, and the local-only infrastructure this
iteration needs — no application logic yet.

- [X] T001 Create `backend/`, `frontend/`, `eval/`, `infra/` directory skeletons per plan.md's Project Structure
- [X] T002 [P] Initialize backend Python project (`backend/pyproject.toml`) with FastAPI, Pydantic v2, SQLAlchemy[asyncio], aiosqlite, alembic, azure-identity, openai, azure-search-documents, azure-keyvault-secrets, bcrypt, pyjwt, langsmith, azure-monitor-opentelemetry, pytest, pytest-asyncio, httpx, ruff, black
- [X] T003 [P] Initialize frontend project (`frontend/package.json`) with React 18, TypeScript, Vite, React Router, eslint, prettier, vitest, @testing-library/react
- [X] T004 [P] Configure backend lint/format (ruff + black) in `backend/pyproject.toml`
- [X] T005 [P] Configure frontend lint/format (`frontend/.eslintrc.cjs`, `frontend/.prettierrc`)
- [X] T006 [P] Create `backend/.env.example` documenting non-secret settings only (`AZURE_OPENAI_ENDPOINT` for the existing `aoai-jab4fcusuxtqs` resource, `AZURE_OPENAI_DEPLOYMENT=gpt-5.1`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`, `KEY_VAULT_URI`) plus a comment pointing at the manual LangSmith-key step from T012
- [X] T007 [P] Write `infra/main.bicep` orchestrating `search.bicep`, `keyvault.bicep`, `monitoring.bicep`, and `roles.bicep`, taking `principalId`, `existingOpenAiName`, and `existingOpenAiResourceGroup` parameters — no App Service or new Azure OpenAI module
- [X] T008 [P] Write `infra/modules/search.bicep` (the one new resource this project provisions: Azure AI Search, Free SKU)
- [X] T009 [P] Write `infra/modules/keyvault.bicep`: RBAC-mode Key Vault that also generates a random JWT signing secret (secure Bicep parameter/`uniqueString`-derived value) and writes it as a Key Vault secret resource at provision time — closes the "who populates the JWT secret" gap from `/speckit-analyze` finding U1
- [X] T010 [P] Write `infra/modules/monitoring.bicep` (Application Insights + Log Analytics workspace)
- [X] T011 Write `infra/modules/roles.bicep` assigning Search Index Data Contributor/Reader and Key Vault Secrets User on the new resources, and Cognitive Services OpenAI User on the *existing* `aoai-jab4fcusuxtqs` resource, all scoped to the `principalId` parameter (the developer's `az login` object ID for now) (depends on T008–T010)
- [X] T012 [P] Document the one-time manual step to set the LangSmith API key into the provisioned Key Vault (`az keyvault secret set --vault-name ... --name LangSmithApiKey --value ...`) in `quickstart.md` — closes the LangSmith-key half of finding U1
- [X] T013 [P] Add `.github/workflows/ci.yml` running ruff + black --check + pytest (backend), eslint + prettier --check + vitest (frontend), and a secret-scan step (e.g., gitleaks) — all four gate merge per constitution Principle IV

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure every user story depends on (DB, auth primitives,
error handling, app wiring, telemetry).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T014 Implement async SQLAlchemy engine/session setup in `backend/src/core/db.py`
- [X] T015 Initialize Alembic in `backend/alembic/` wired to the SQLAlchemy models metadata
- [X] T016 Define the `User` ORM model (id, unique email, unique username, password_hash, role, created_at) in `backend/src/models/db.py`
- [X] T017 Generate and apply the initial Alembic migration for the `users` table in `backend/alembic/versions/`
- [X] T018 [P] Define the shared `Error` response Pydantic schema in `backend/src/models/schemas.py`
- [X] T019 Implement a custom exception hierarchy and FastAPI exception handlers mapping internal failures to non-leaking `Error` responses in `backend/src/core/errors.py`
- [X] T020 Implement JWT encode/decode utilities and the `get_current_user` / `require_admin` FastAPI dependencies in `backend/src/core/security.py`
- [X] T021 Implement the settings loader in `backend/src/core/config.py`: non-secret settings (existing Azure OpenAI endpoint/deployment, new Azure AI Search endpoint) plus Key Vault secret resolution (JWT signing key, LangSmith API key) via `DefaultAzureCredential`
- [X] T022 Create the FastAPI app factory with router-registration skeleton and CORS configured for the local frontend dev server in `backend/src/main.py`
- [X] T023 Bootstrap Application Insights/OpenTelemetry auto-instrumentation and a request-stage-tagging middleware (`upload`/`retrieval`/`generation`) in `backend/src/core/telemetry.py`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Register and Log In to a Personal Account (Priority: P1) 🎯 MVP (part 1 of 2)

**Goal**: A visitor can register with a unique email, username, and password; a
registered user can log in with either identifier plus the password and land in a
workspace scoped to only their own data.

**Independent Test**: Register a new account, log out, log back in once with the
registered email and once with the registered username (same password); confirm both
succeed and an incorrect password is rejected.

### Tests for User Story 1

> Write these tests FIRST; confirm they FAIL before implementation.

- [X] T024 [P] [US1] Contract test `POST /auth/register` (success, duplicate email/username → 409, malformed input → 422) in `backend/tests/contract/test_auth_register.py`
- [X] T025 [P] [US1] Contract test `POST /auth/login` (success via email, success via username, wrong password / unrecognized identifier → single generic 401) in `backend/tests/contract/test_auth_login.py`
- [X] T026 [P] [US1] Integration test: register → log out → log in with email → log in with username in `backend/tests/integration/test_auth_flow.py`
- [X] T027 [P] [US1] Unit tests for bcrypt hashing and minimum password-length validation in `backend/tests/unit/test_auth_service.py`

### Implementation for User Story 1

- [X] T028 [P] [US1] Add `RegisterRequest`, `LoginRequest`, `AuthToken` Pydantic schemas in `backend/src/models/schemas.py`
- [X] T029 [US1] Implement `backend/src/services/auth_service.py`: `register_user` (bcrypt hash, DB unique-constraint conflict → 409) and `authenticate_user` (email-or-username lookup, single generic 401 on any mismatch) (depends on T016, T020, T028)
- [X] T030 [US1] Implement `POST /auth/register` and `POST /auth/login` routes in `backend/src/api/auth.py` (depends on T029)
- [X] T031 [US1] Register the auth router in `backend/src/main.py` (depends on T022, T030)
- [X] T032 [P] [US1] Implement `RegisterForm` component in `frontend/src/components/RegisterForm.tsx`
- [X] T033 [P] [US1] Implement `LoginForm` component in `frontend/src/components/LoginForm.tsx`
- [X] T034 [US1] Implement the auth API client and auth context (stores the JWT, attaches it as an Authorization header) in `frontend/src/services/auth.ts`
- [X] T035 [US1] Implement `Register` and `Login` pages wired to the components/context above in `frontend/src/pages/Register.tsx` and `frontend/src/pages/Login.tsx` (depends on T032, T033, T034)

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Ask Grounded, Cited Questions Over Uploaded Documents (Priority: P1) 🎯 MVP (part 2 of 2)

**Goal**: A logged-in user uploads documents and asks questions, receiving a
structured, schema-validated, cited answer grounded only in their own documents (or an
explicit no-answer-found signal), with uploads/questions rate-limited and deleted
documents' citations retained in history.

**Independent Test**: Upload a small document, ask a question whose answer is in it,
verify the response is schema-valid, contains an answer, and cites that document.

### Tests for User Story 2

- [X] T036 [P] [US2] Contract test `POST /documents` (accepted; empty/corrupted/password-protected/oversized(>10MB)/unsupported-format → 400; over rate limit → 429) in `backend/tests/contract/test_documents_upload.py`
- [X] T037 [P] [US2] Contract test `GET /documents` and `DELETE /documents/{id}` (list own only, 404 for others' documents) in `backend/tests/contract/test_documents_manage.py`
- [X] T038 [P] [US2] Contract test `POST /queries` (answered with citations; no_answer_found; empty question → 422; over rate limit → 429) in `backend/tests/contract/test_queries_ask.py`
- [X] T039 [P] [US2] Contract test `POST /queries` retrieval/generation failure → structured `502` with a non-leaking message (matches the `502` response documented in contracts/openapi.yaml) in `backend/tests/contract/test_queries_failure.py` — addresses `/speckit-analyze` finding E1
- [X] T040 [P] [US2] Integration test: upload → ask → structured, cited answer (happy path) in `backend/tests/integration/test_ask_grounded.py`
- [X] T041 [P] [US2] Integration test: no documents uploaded yet, and question with no answer in the corpus → explicit no_answer_found in `backend/tests/integration/test_ask_no_answer.py`
- [X] T042 [P] [US2] Integration test: delete a cited document → citation retained in history marked `source_removed: true`, document no longer retrievable in `backend/tests/integration/test_document_delete.py`
- [X] T043 [P] [US2] Integration test: per-user upload and question rate limits (429 with limit/reset info) in `backend/tests/integration/test_rate_limit.py`
- [X] T044 [P] [US2] Unit tests for document validation (empty/corrupted/password-protected/oversized/unsupported format) in `backend/tests/unit/test_document_service.py`
- [X] T045 [P] [US2] Unit tests asserting the retrieval query always includes the mandatory `user_id` + `status=active` filter (never omitted, never client-overridable) in `backend/tests/unit/test_retrieval_service.py`
- [X] T046 [P] [US2] Unit tests asserting every `document_service`/`query_service` read and write function requires and applies the authenticated `user_id` (list/get/delete document, list/get query) — mirrors T045's pattern for the SQLite-backed side of FR-006/SC-007 in `backend/tests/unit/test_data_isolation.py` — addresses `/speckit-analyze` finding E2
- [X] T047 [P] [US2] Unit tests asserting an `Answer` cannot be persisted with `groundedness_status=grounded` and zero citations (must be rejected or downgraded to `no_answer_found`) in `backend/tests/unit/test_answer_guard.py` — addresses `/speckit-analyze` finding U2

### Implementation for User Story 2

- [X] T048 [P] [US2] Define `Document`, `Query`, `Answer`, `Citation`, `RateLimitCounter` ORM models in `backend/src/models/db.py`
- [X] T049 [US2] Generate and apply the Alembic migration for `documents`/`queries`/`answers`/`citations`/`rate_limit_counters` tables in `backend/alembic/versions/` (depends on T048)
- [X] T050 [P] [US2] Add `Document`, `QueryRequest`, `QueryRecord`, `Citation`, `ResponseMetadata`, and the Structured-Outputs-bound `Answer` Pydantic schemas in `backend/src/models/schemas.py`
- [X] T051 [US2] Implement `backend/src/services/retrieval_service.py`: ensure the Azure AI Search index exists, hybrid (vector+keyword) query with the mandatory server-injected `user_id`+`status` filter, passage upsert on ingest and removal on delete, wrapping search-service failures as a classified retrieval error (feeds T039) (depends on T021)
- [X] T052 [US2] Implement `backend/src/services/generation_service.py`: Azure OpenAI Structured Outputs call against the existing `aoai-jab4fcusuxtqs` deployment producing the `Answer`/`Citation`/`ResponseMetadata` shape, computing `context_window_utilization`, wrapping generation-service failures as a classified generation error (feeds T039) (depends on T050, T021)
- [X] T053 [US2] Implement `backend/src/services/document_service.py`: format/size(10MB)/corruption/password-protection validation, parse+chunk, delegate to `retrieval_service` for indexing/deletion, status transitions (`processing→ready|failed`, `ready→deleted`), all reads/writes scoped by `user_id` (depends on T048, T051)
- [X] T054 [US2] Implement `backend/src/services/rate_limit_service.py`: rolling-24h check-and-increment for uploads (50/day) and questions (200/day) (depends on T048)
- [X] T055 [US2] Implement `backend/src/services/query_service.py`: `ask_question` orchestrating rate-limit check → retrieval → generation → the zero-citation groundedness guard (T047) → persistence, all scoped by `user_id` (depends on T051, T052, T054)
- [X] T056 [US2] Implement `POST /documents`, `GET /documents`, `DELETE /documents/{id}` routes in `backend/src/api/documents.py` (depends on T053, T054)
- [X] T057 [US2] Implement `POST /queries` route calling `query_service.ask_question`, mapping retrieval/generation failures to the `502` contract response, in `backend/src/api/queries.py` (depends on T055)
- [X] T058 [US2] Register the documents and queries routers in `backend/src/main.py` (depends on T022, T056, T057)
- [X] T059 [P] [US2] Implement `DocumentUpload` component in `frontend/src/components/DocumentUpload.tsx`
- [X] T060 [P] [US2] Implement `ChatInput`, `AnswerCard`, `CitationList` components in `frontend/src/components/`
- [X] T061 [US2] Implement the `Workspace` page (upload + ask) wired to the API client in `frontend/src/pages/Workspace.tsx` (depends on T059, T060)
- [ ] T062 [US2] Run `backend/src/services/retrieval_service.py` and `generation_service.py` once against the real existing Azure OpenAI resource and the newly provisioned Azure AI Search resource (via `az login`) to confirm managed-identity-style auth works end-to-end locally (depends on T051, T052, T011) — **not run**: this development environment has no `az login`/outbound network access to real Azure resources; all other US2 tasks were validated against the fake in-memory search/generation doubles in `backend/tests/conftest.py`. Run this manually once Azure access is available.

**Checkpoint**: User Stories 1 and 2 together form a locally runnable, demoable MVP.

---

## Phase 5: User Story 3 - Revisit Past Queries and Answers (Priority: P2)

**Goal**: A user can browse their own past questions, answers, and citations,
most-recent-first, and revisit any one of them exactly as it was originally returned.

**Independent Test**: Ask a question, confirm it appears in history, and confirm
revisiting it returns the identical structured answer and citations.

### Tests for User Story 3

- [ ] T063 [P] [US3] Contract test `GET /queries` (most-recent-first ordering; empty array — not an error — for a new account) in `backend/tests/contract/test_queries_history.py`
- [ ] T064 [P] [US3] Contract test `GET /queries/{id}` (exact replay of the original answer; 404 for another user's query) in `backend/tests/contract/test_queries_detail.py`
- [ ] T065 [P] [US3] Integration test: ask a question → it appears in `GET /queries` → `GET /queries/{id}` returns the identical answer/citations in `backend/tests/integration/test_history_flow.py`

### Implementation for User Story 3

- [ ] T066 [US3] Add `list_queries`/`get_query` functions (user-scoped, most-recent-first, explicit empty-state) to `backend/src/services/query_service.py` (depends on T055)
- [ ] T067 [US3] Implement `GET /queries` and `GET /queries/{id}` routes in `backend/src/api/queries.py` (depends on T066)
- [ ] T068 [P] [US3] Implement `HistoryList` component in `frontend/src/components/HistoryList.tsx`
- [ ] T069 [US3] Implement the `History` page wired to `GET /queries` and `GET /queries/{id}` in `frontend/src/pages/History.tsx` (depends on T068)

**Checkpoint**: User Stories 1–3 all independently functional.

---

## Phase 6: User Story 4 - Compare Two System Versions Against a Benchmark Dataset (Priority: P2, admin/evaluator only)

**Goal**: An administrator/evaluator maintains a benchmark dataset and runs two named
system versions against it, receiving per-question and aggregate correctness/
relevance/groundedness scores and a clear winner; regular users are rejected.

**Independent Test**: Run two versions against a small fixed dataset and confirm a
per-question and aggregate scored comparison identifying the better-performing version.

### Tests for User Story 4

- [ ] T070 [P] [US4] Contract test admin-only enforcement (403 for a non-admin caller) across all `/admin/eval/*` routes in `backend/tests/contract/test_admin_eval_authz.py`
- [ ] T071 [P] [US4] Contract test `POST`/`GET /admin/eval/dataset-items` in `backend/tests/contract/test_admin_eval_dataset.py`
- [ ] T072 [P] [US4] Contract test `POST /admin/eval/comparison-runs` and `GET /admin/eval/comparison-runs/{id}` (winner, per-version aggregate scores, `partial` status when a version fails to answer some questions) in `backend/tests/contract/test_admin_eval_runs.py`
- [ ] T073 [P] [US4] Integration test: end-to-end comparison run against a small fixture dataset, including one question one version fails to answer in `backend/tests/integration/test_comparison_run.py`
- [ ] T074 [P] [US4] Unit tests for the correctness/relevance/groundedness evaluator functions in `eval/tests/test_evaluators.py`
- [ ] T075 [P] [US4] Test that the admin-provisioning script (T077) produces an account whose role is `admin` and that account passes the T070 authz checks, in `backend/tests/integration/test_admin_provisioning.py` — addresses `/speckit-analyze` finding U3

### Implementation for User Story 4

- [ ] T076 [P] [US4] Define the `ComparisonRun` ORM model in `backend/src/models/db.py`
- [ ] T077 [US4] Implement `backend/scripts/create_admin.py`: a CLI that promotes an existing user (by email/username) or creates a new one directly with `role=admin`, for out-of-band administrator provisioning per spec.md's Assumptions (depends on T016) — addresses `/speckit-analyze` finding U3
- [ ] T078 [US4] Generate and apply the Alembic migration for the `comparison_runs` table in `backend/alembic/versions/` (depends on T076)
- [ ] T079 [P] [US4] Add `DatasetItem`, `ComparisonRunRequest`, `ComparisonRun` Pydantic schemas in `backend/src/models/schemas.py`
- [ ] T080 [P] [US4] Implement `eval/dataset_sync.py` pushing admin-curated dataset items into a LangSmith dataset
- [ ] T081 [P] [US4] Implement `eval/evaluators/correctness.py` (LLM-as-judge against the expected answer, via the existing Azure OpenAI deployment)
- [ ] T082 [P] [US4] Implement `eval/evaluators/relevance.py` (LLM-as-judge against the original question)
- [ ] T083 [P] [US4] Implement `eval/evaluators/groundedness.py` (citation-coverage check with LLM-as-judge fallback for paraphrased claims)
- [ ] T084 [US4] Implement `eval/run_experiment.py` running two named versions through LangSmith's `evaluate()`, producing per-question and aggregate scores, recording non-responses as failures rather than omissions (depends on T081, T082, T083)
- [ ] T085 [US4] Implement `backend/src/services/eval_service.py` orchestrating dataset-item CRUD and triggering `run_experiment`, persisting `ComparisonRun` summaries (depends on T076, T084)
- [ ] T086 [US4] Implement `/admin/eval/dataset-items` and `/admin/eval/comparison-runs` routes, gated by `require_admin`, in `backend/src/api/admin_eval.py` (depends on T085, T020)
- [ ] T087 [US4] Register the admin_eval router in `backend/src/main.py` (depends on T022, T086)
- [ ] T088 [P] [US4] Implement `AdminDashboard` / comparison-run view components in `frontend/src/components/AdminDashboard.tsx`
- [ ] T089 [US4] Implement the `AdminEval` page wired to the admin eval endpoints in `frontend/src/pages/AdminEval.tsx` (depends on T088)

**Checkpoint**: User Stories 1–4 all independently functional.

---

## Phase 7: User Story 5 - Monitor Operational Health in Production (Priority: P3, admin/evaluator only)

**Goal**: An administrator/evaluator can view response latency, token consumption, and
error rate for a recent time window, broken down by request stage; regular users are
rejected.

**Independent Test**: Generate a mix of successful and failing requests and confirm
latency, token consumption, and error rate are all observable, broken down by stage.

### Tests for User Story 5

- [ ] T090 [P] [US5] Contract test `GET /admin/metrics` (403 for non-admin; 200 shape with per-stage breakdown for admin) in `backend/tests/contract/test_admin_metrics.py`
- [ ] T091 [P] [US5] Integration test: mixed success/failure traffic is reflected in metrics, data no more than 5 minutes stale in `backend/tests/integration/test_metrics_visibility.py`

### Implementation for User Story 5

- [ ] T092 [US5] Implement `backend/src/services/metrics_service.py` querying Application Insights for latency/token/error-rate figures by stage and time window (depends on T023)
- [ ] T093 [US5] Implement `GET /admin/metrics` route, gated by `require_admin`, in `backend/src/api/admin_metrics.py` (depends on T092, T020)
- [ ] T094 [US5] Register the admin_metrics router in `backend/src/main.py` (depends on T022, T093)
- [ ] T095 [P] [US5] Implement the `AdminMetrics` page/components in `frontend/src/pages/AdminMetrics.tsx`

**Checkpoint**: All five user stories independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Coverage gaps, hardening, and end-to-end local validation across all
stories.

- [ ] T096 [P] Fill remaining backend unit-test coverage for edge cases across services (empty/malformed inputs) in `backend/tests/unit/`
- [ ] T097 [P] Fill remaining frontend Vitest coverage for `DocumentUpload`/`HistoryList`/`AdminDashboard` in `frontend/tests/` (`RegisterForm`/`LoginForm` were already covered in US1, `frontend/tests/components/`)
- [ ] T098 Run the full `quickstart.md` local-validation scenario set end-to-end (including the Infrastructure section's `az deployment group create` step and manual scenarios 1–6)
- [ ] T099 Security hardening pass: verify no failure path leaks internal details, cross-checked against FR-004/FR-009/FR-021
- [ ] T100 Performance check: measure question-answer latency against the ≥95%-within-15s target (SC-011) with a representative document set, running locally against the real Azure AI Search/Azure OpenAI resources
- [ ] T101 [P] Write `backend/README.md` and `frontend/README.md` covering local setup (uvicorn + Vite, `az login`), testing, and the current no-App-Service scope (linking to quickstart.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends only on Foundational.
- **User Story 2 (Phase 4)**: Depends only on Foundational. Functionally independent of
  US1's implementation, but both are P1 and together form the MVP (US2's contract/
  integration tests assume an authenticated caller, i.e., US1 exists). T062 additionally
  depends on T011 (RBAC role assignments) having been applied via `infra/main.bicep`.
- **User Story 3 (Phase 5)**: Depends on Foundational; reuses `query_service.py` created
  in US2 (Phase 4) — build after US2.
- **User Story 4 (Phase 6)**: Depends on Foundational (specifically `require_admin` from
  T020); independent of US2/US3's data, but needs a working Q&A loop to have something
  meaningful to benchmark, and needs T077 (admin provisioning) before any admin-gated
  route can be exercised end-to-end.
- **User Story 5 (Phase 7)**: Depends on Foundational's telemetry bootstrap (T023);
  independent of all other stories' data model.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### Within Each User Story

- Tests are written first and must fail before implementation begins.
- Models before services; services before routes; routes before frontend wiring.
- Story is complete and independently checkpointed before moving to the next priority.

### Parallel Opportunities

- All `[P]`-marked Setup tasks (T002–T010, T012, T013) can run in parallel.
- Within Foundational, T018 can run in parallel with T014–T017 (different files).
- Once Foundational completes, US1 and US2 can be staffed in parallel (both depend only
  on Foundational); US3 should follow US2; US4 and US5 can be staffed in parallel with
  each other and with US1–US3.
- All `[P]`-marked tests within a story can run in parallel with each other.
- All `[P]`-marked model/schema tasks within a story can run in parallel.

---

## Parallel Example: User Story 2

```bash
# Launch all US2 tests together (after Foundational is complete):
Task: "Contract test POST /documents in backend/tests/contract/test_documents_upload.py"
Task: "Contract test GET/DELETE /documents in backend/tests/contract/test_documents_manage.py"
Task: "Contract test POST /queries in backend/tests/contract/test_queries_ask.py"
Task: "Contract test POST /queries failure path (502) in backend/tests/contract/test_queries_failure.py"
Task: "Integration test upload-ask-cite happy path in backend/tests/integration/test_ask_grounded.py"
Task: "Integration test no-answer scenarios in backend/tests/integration/test_ask_no_answer.py"
Task: "Integration test document delete in backend/tests/integration/test_document_delete.py"
Task: "Integration test rate limiting in backend/tests/integration/test_rate_limit.py"
Task: "Unit tests for document validation in backend/tests/unit/test_document_service.py"
Task: "Unit tests for mandatory retrieval filter in backend/tests/unit/test_retrieval_service.py"
Task: "Unit tests for data isolation across document/query services in backend/tests/unit/test_data_isolation.py"
Task: "Unit tests for the zero-citation groundedness guard in backend/tests/unit/test_answer_guard.py"

# Launch US2 models/schemas together:
Task: "Define Document/Query/Answer/Citation/RateLimitCounter ORM models in backend/src/models/db.py"
Task: "Add Document/QueryRequest/QueryRecord/Citation/ResponseMetadata/Answer schemas in backend/src/models/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 only)

1. Complete Phase 1: Setup (including provisioning `infra/main.bicep` once, so T062 can
   run against real Azure resources).
2. Complete Phase 2: Foundational (blocks everything).
3. Complete Phase 3: User Story 1 (accounts).
4. Complete Phase 4: User Story 2 (core Q&A loop).
5. **STOP and VALIDATE**: run the Phase 3/4 independent tests and the relevant
   quickstart.md scenarios (1–2, 4, 6). This is a usable, locally-runnable product —
   no deployment step is required to demo it.

### Incremental Delivery

1. Setup + Foundational → foundation ready (Azure AI Search + Key Vault + App Insights
   provisioned; existing Azure OpenAI resource accessible via RBAC).
2. Add US1 → test independently.
3. Add US2 → test independently → **MVP runnable locally**.
4. Add US3 → test independently → demo (history).
5. Add US4 → test independently → demo (quality measurement, admin-only — provision
   the first admin via T077).
6. Add US5 → test independently → demo (ops visibility, admin-only).
7. Polish → full quickstart.md pass. Azure App Service deployment is a future
   amendment, not part of this task list.

Each stage corresponds to constitution Principle V: one reviewable PR per stage, CI
green (Principle IV) before merge, project left in a working state throughout.

### Parallel Team Strategy

With multiple developers, after Foundational completes:

- Developer A: User Story 1, then User Story 3 (builds on US2's query_service).
- Developer B: User Story 2 (core loop — the highest-risk, highest-value piece).
- Developer C: User Story 4, then User Story 5 (both admin-only, both depend only on
  Foundational's `require_admin`).

---

## Notes

- `[P]` tasks touch different files and have no unmet dependency.
- `[Story]` label maps every user-story-phase task to its spec.md story for traceability.
- Tests are written first and must fail before the corresponding implementation task.
- Commit after each task or logical group, per constitution Principle V (one commit per
  stage) — open a PR as soon as a story's Setup/Foundational-through-Checkpoint tasks
  pass CI.
- Avoid: vague tasks, two tasks editing the same file marked `[P]`, and cross-story
  dependencies that would break a story's ability to be demoed on its own.
- Azure App Service, `azure.yaml`, and any `azd deploy` step are intentionally absent
  from this task list per the current plan.md scope; they will appear in a future
  tasks.md regeneration once deployment is requested.
</content>
