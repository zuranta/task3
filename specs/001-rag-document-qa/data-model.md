# Phase 1 Data Model: RAG Document Q&A Application

Entities derived from spec.md's Key Entities section, refined with concrete fields,
types, relationships, validation rules, and state transitions. Storage location (SQLite
vs. Azure AI Search vs. Application Insights vs. LangSmith) is noted per entity — see
research.md for the rationale behind each.

## User

**Storage**: SQLite (`users` table)

| Field | Type | Rules |
|---|---|---|
| id | integer/uuid, PK | generated |
| email | string, unique, indexed | valid email format; case-insensitive uniqueness |
| username | string, unique, indexed | 3–32 chars, alphanumeric + underscore |
| password_hash | string | bcrypt hash (cost 12); never the plaintext password |
| role | enum(`user`, `admin`) | default `user`; `admin` accounts provisioned out-of-band (spec Assumptions) |
| created_at | datetime | set on insert, immutable |

**Relationships**: one-to-many → Document, Query, RateLimitCounter.

**Validation** (FR-001, FR-003, FR-005): email and username each unique via DB-level
unique constraints (not just app-level checks, to close registration races); password
≥ 8 characters enforced before hashing.

## Document

**Storage**: SQLite (`documents` table) for metadata; extracted content lives in Azure
AI Search (see Source Passage below). Raw uploaded bytes are not persisted (research.md §5).

| Field | Type | Rules |
|---|---|---|
| id | integer/uuid, PK | generated |
| user_id | FK → User.id | required; every query filters on this |
| original_filename | string | as provided at upload |
| format | enum(`pdf`, `docx`, `txt`, `md`) | validated against FR-008's supported set |
| status | enum(`processing`, `ready`, `failed`, `deleted`) | see state transitions below |
| failure_reason | string, nullable | set only when status = `failed`; user-facing, non-leaking (FR-009) |
| uploaded_at | datetime | set on insert |

**State transitions**:

```
processing --(parse/chunk/embed/index succeed)--> ready
processing --(empty/corrupted/unsupported/password-protected)--> failed
ready --(user deletes)--> deleted
```

`failed` and `deleted` are terminal; a `failed` upload cannot be retried in place (the
user re-uploads). Deleting a document removes its Source Passages from the Azure AI
Search index (so it can no longer be retrieved, FR-010) but its `documents` row is kept
(status = `deleted`) so existing Citations can still resolve their source document's
filename for display.

## Source Passage

**Storage**: Azure AI Search index (not SQLite) — one search index shared across all
users and documents.

| Field | Type | Rules |
|---|---|---|
| id | string, key | `{document_id}_{chunk_index}` |
| document_id | string, filterable | joins back to `documents.id` |
| user_id | string, filterable | **mandatory filter on every query** (research.md §3) |
| status | string, filterable | mirrors owning Document's status; queries filter `status eq 'active'` |
| chunk_index | int | position within the document |
| location_label | string | human-readable locator (e.g., page/section) surfaced in citations |
| content | string, searchable | chunk text (BM25 keyword search) |
| content_vector | vector | embedding of `content` (vector/hybrid search) |

## Query

**Storage**: SQLite (`queries` table)

| Field | Type | Rules |
|---|---|---|
| id | integer/uuid, PK | generated |
| user_id | FK → User.id | required; every read scoped to this |
| question_text | string | as submitted; non-empty |
| status | enum(`answered`, `no_answer_found`, `failed`) | terminal once set |
| created_at | datetime | set on insert |

**Relationships**: one-to-one → Answer (present only when status ≠ `failed`).

## Answer

**Storage**: SQLite (`answers` table)

| Field | Type | Rules |
|---|---|---|
| id | integer/uuid, PK | generated |
| query_id | FK → Query.id, unique | one Answer per Query |
| answer_text | string | empty/omitted when status = `no_answer_found` |
| groundedness_status | enum(`grounded`, `no_answer_found`) | FR-014, FR-017 |
| prompt_tokens | int | from Azure OpenAI usage |
| completion_tokens | int | from Azure OpenAI usage |
| total_tokens | int | from Azure OpenAI usage |
| context_window_utilization | float (0–1) | `total_tokens / model_context_window` |
| created_at | datetime | set on insert; never mutated on replay (FR-020) |

**Relationships**: one-to-many → Citation.

**Validation**: An Answer with `groundedness_status = grounded` MUST have at least one
Citation (FR-015); this is enforced at the point of persistence (reject/flag a
zero-citation "grounded" answer rather than saving it as such).

## Citation

**Storage**: SQLite (`citations` table)

| Field | Type | Rules |
|---|---|---|
| id | integer/uuid, PK | generated |
| answer_id | FK → Answer.id | required |
| document_id | FK → Document.id | required (row persists even if Document later deleted) |
| location_label | string | copied from the Source Passage at generation time |
| source_removed | boolean, derived | computed as `document.status == 'deleted'` at read time; not independently writable |

## Evaluation Dataset Item

**Storage**: LangSmith dataset (system of record; research.md §9) — not duplicated in
SQLite. Referenced by name/ID from `eval/dataset_sync.py` and `run_experiment.py`.

| Field | Type | Rules |
|---|---|---|
| question_text | string | example question |
| expected_answer | string | reference answer for correctness scoring |
| expected_source_reference | string, optional | expected supporting document/passage, if known |

## Comparison Run

**Storage**: SQLite (`comparison_runs` table) holds the summary; full per-question
results live in the corresponding LangSmith experiments.

| Field | Type | Rules |
|---|---|---|
| id | integer/uuid, PK | generated |
| version_a_label | string | e.g., prompt/retrieval-config identifier |
| version_b_label | string | e.g., prompt/retrieval-config identifier |
| langsmith_experiment_id_a | string | link to full per-question detail |
| langsmith_experiment_id_b | string | link to full per-question detail |
| aggregate_score_a | JSON (`{correctness, relevance, groundedness}`) | 0–1 each |
| aggregate_score_b | JSON (`{correctness, relevance, groundedness}`) | 0–1 each |
| winner | enum(`a`, `b`, `tie`) | FR-025 |
| status | enum(`running`, `completed`, `partial`) | `partial` when a version failed to answer some questions (FR-026) |
| created_by | FK → User.id | must have role = `admin` (FR-007) |
| started_at | datetime | |
| completed_at | datetime, nullable | null while `running` |

## Rate Limit Counter

**Storage**: SQLite (`rate_limit_counters` table). Introduced to implement FR-012; not
named as an entity in spec.md, but required by it.

| Field | Type | Rules |
|---|---|---|
| user_id | FK → User.id | composite key with counter_type |
| counter_type | enum(`upload`, `question`) | composite key with user_id |
| window_start | datetime | start of the current rolling 24h window |
| count | int | requests made in the current window |

## Operational Metric Record

**Storage**: Application Insights telemetry (`requests`/`dependencies`/custom metrics),
per research.md §10 — **not** a SQLite table. FR-027/028 are satisfied by querying
Application Insights (via its API/Log Analytics) filtered by request stage and time
window, rather than a bespoke app-database table.
</content>
