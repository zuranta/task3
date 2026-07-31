# Backend — RAG Document Q&A Application

FastAPI + SQLAlchemy (async) + Azure AI Search + Azure OpenAI. See
[`../specs/001-rag-document-qa/plan.md`](../specs/001-rag-document-qa/plan.md) for the
full architecture and [`../specs/001-rag-document-qa/quickstart.md`](../specs/001-rag-document-qa/quickstart.md)
for end-to-end manual validation scenarios.

## Local setup

Prerequisites: Python 3.12, an Azure subscription, `az login` (so
`DefaultAzureCredential` can resolve your developer identity locally — see
**Azure / no App Service yet** below).

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env        # fill in the real endpoints/URIs — see .env.example's comments
alembic upgrade head
uvicorn src.main:app --reload
```

Or, from the repo root: `make install_backend`, `make migrate`, `make run_backend`
(the last one runs migrations then starts uvicorn with `--env-file .env`, so anything
you add to `.env` is picked up on the next restart).

Backend listens on `http://127.0.0.1:8000`; interactive API docs at `/docs`.

### Required settings (`.env`)

Non-secret settings only (constitution Principle II — never commit a populated
`.env`). See `.env.example` for the full list and where each value comes from
(mostly `infra/main.bicep` deployment outputs). Two secrets have no
managed-identity equivalent and are resolved from Key Vault at startup instead of
being env vars: the JWT signing secret (written automatically by `keyvault.bicep`)
and the LangSmith API key (set manually once — see quickstart.md's Infrastructure
section).

## Testing

```bash
pytest                 # unit + contract + integration; success, failure, and
                        # empty/malformed-input cases per feature
ruff check . && black --check .
```

Or from the repo root: `make test_backend`, `make lint_backend`.

All Azure dependencies (Azure OpenAI, Azure AI Search, Key Vault, Application
Insights, LangSmith) are mocked at the service boundary in tests — `pytest` never
makes a real network call, so it runs the same with or without `az login`.

## Azure / no App Service yet

Every credential in `backend/src/` authenticates via `DefaultAzureCredential`,
which resolves to your `az login` session in this local-only iteration. There is
no Azure App Service (or other hosting) provisioned yet — deployment is deferred
to a future amendment (see plan.md's Deployment Scope). When that's added, the
only change needed is pointing `infra/modules/roles.bicep`'s `principalId` at the
new managed identity instead of a developer's object ID; no application code
changes, since the same `DefaultAzureCredential` call resolves a managed identity
automatically.

## Known limitation: search-index propagation lag

Azure AI Search indexing is near-real-time, not synchronous. A document can reach
`status: ready` in the database microseconds before its passages are actually
searchable, so a question asked immediately after upload can occasionally come
back `no_answer_found` even though the content is genuinely there — a retry a few
seconds later succeeds. This doesn't affect anything already in the index (only
the immediate aftermath of a fresh upload), and isn't currently mitigated in code.
