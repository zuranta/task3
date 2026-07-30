# Quickstart: RAG Document Q&A Application

Validates the feature end-to-end, locally and against deployed Azure infrastructure.
See [data-model.md](./data-model.md) for entity detail and
[contracts/openapi.yaml](./contracts/openapi.yaml) for the exact request/response
shapes referenced below.

## Prerequisites

- Python 3.12, Node 20 LTS, an Azure subscription, `az` CLI logged in (`az login`) so
  `DefaultAzureCredential` can resolve your developer credential locally.
- Access to the **existing** Azure OpenAI resource `aoai-jab4fcusuxtqs` (`gpt-5.1`
  deployment) — this project does not provision its own; ask whoever owns it to grant
  your `az login` principal the `Cognitive Services OpenAI User` role, or run
  `infra/main.bicep` (see Infrastructure below), which does this for you.
- Run `infra/main.bicep` once to provision the one new Azure AI Search (Free tier)
  resource this project needs, plus Key Vault and Application Insights.

## Local setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # non-secret settings only — see constitution Technology & Security Standards
alembic upgrade head
uvicorn src.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Required non-secret environment variables (`.env.example`): `AZURE_OPENAI_ENDPOINT`
(the existing `aoai-jab4fcusuxtqs` resource's endpoint), `AZURE_OPENAI_DEPLOYMENT`
(`gpt-5.1`), `AZURE_SEARCH_ENDPOINT` (this project's new Free-tier resource, from the
`infra/main.bicep` output), `AZURE_SEARCH_INDEX_NAME`, `KEY_VAULT_URI` (used to resolve
the JWT signing secret and the LangSmith API key at startup — neither is ever an env
var value directly). All Azure calls authenticate via `DefaultAzureCredential`, which
resolves to your `az login` session for this local-only iteration.

## Automated tests

```bash
# Backend: unit + contract + integration, success and failure/empty/malformed cases
cd backend && pytest

# Frontend
cd frontend && npm run test
```

## Manual validation scenarios

Each scenario maps to a spec.md user story / acceptance scenario.

1. **Register & log in (User Story 1)**
   - `POST /api/v1/auth/register` with a unique email/username/password → `201` + token.
   - `POST /api/v1/auth/login` with the **username** (not email) + correct password →
     `200` + token.
   - Repeat login with a wrong password → `401` with the generic "invalid credentials"
     message (confirm it does not say *which* field was wrong).
   - Re-register with the same email → `409` conflict error.

2. **Upload → ask → cited answer (User Story 2)**
   - Upload a small `.txt` file containing a known fact via `POST /documents`, poll
     `GET /documents` until `status: ready`.
   - `POST /queries` with a question whose answer is in that fact → `200`, `status:
     answered`, `citations` non-empty and pointing at the uploaded document.
   - Ask an unrelated question → `status: no_answer_found`, no fabricated answer.
   - Upload a corrupted/empty file → `400` with a specific, non-leaking error.

3. **Revisit history (User Story 3)**
   - `GET /queries` → the prior question appears, most-recent-first.
   - `GET /queries/{queryId}` → answer/citations exactly match what was originally
     returned.
   - A brand-new account's `GET /queries` → empty array, not an error.

4. **Delete a cited document (FR-010, edge case)**
   - `DELETE /documents/{documentId}` for the document used in step 2.
   - Re-`GET /queries/{queryId}` for that earlier answer → citation still present,
     `source_removed: true`.
   - Ask the same question again → the deleted document's content is no longer
     retrievable (either a new citation set excluding it, or `no_answer_found`).

5. **Admin-only evaluation & metrics (User Stories 4–5, FR-007)**
   - As a **non-admin** account, call `POST /admin/eval/comparison-runs` and
     `GET /admin/metrics` → both `403`.
   - As an **admin** account: add a couple of `DatasetItem`s, start a comparison run
     between two version labels, then `GET` it once `completed`/`partial` and confirm a
     `winner` and per-version aggregate scores are present.
   - `GET /admin/metrics` → latency/token/error-rate figures broken down by stage
     (`upload`/`retrieval`/`generation`).

6. **Rate limiting (FR-012)**
   - Script 201 question submissions for one account within the same day → the 201st
     request returns `429` with the limit and reset time in the error message.

## Evaluation experiment (LangSmith)

```bash
cd eval
python dataset_sync.py           # pushes admin-curated items into the LangSmith dataset
python run_experiment.py \
  --version-a "prompt-v1" \
  --version-b "prompt-v2"
```

Confirm the run produces per-question and aggregate correctness/relevance/groundedness
scores and a clear winner, and that a question one version fails to answer is recorded
as a failure for that version rather than omitted (FR-026).

## Infrastructure (local-only iteration — no App Service yet)

This iteration provisions only what local development needs: one new Azure AI Search
resource, Key Vault, and Application Insights. It reuses the existing Azure OpenAI
resource rather than creating one, and does **not** provision Azure App Service —
deployment/hosting is deferred to a future amendment.

```bash
az login
az deployment group create \
  --resource-group <your-resource-group> \
  --template-file infra/main.bicep \
  --parameters principalId=$(az ad signed-in-user show --query id -o tsv) \
               existingOpenAiName=aoai-jab4fcusuxtqs \
               existingOpenAiResourceGroup=<resource-group-containing-aoai-jab4fcusuxtqs>
```

This grants your own `az login` identity the RBAC roles the app needs (Search Index
Data Contributor/Reader on the new Search resource, Key Vault Secrets User on the new
Key Vault, Cognitive Services OpenAI User on the existing `aoai-jab4fcusuxtqs`
resource) and outputs the new Search endpoint and Key Vault URI to put in `.env`.

The JWT signing secret is generated by `keyvault.bicep` and written into the vault
automatically — no manual step needed for it. The LangSmith API key has no
managed-identity equivalent (it's a third-party credential), so set it into the same
vault once, manually, after the deployment above completes:

```bash
az keyvault secret set \
  --vault-name <keyVaultName-from-the-deployment-output> \
  --name LangSmithApiKey \
  --value <your-langsmith-api-key>
```

Since every credential in the codebase goes through `DefaultAzureCredential`, repeating
scenarios 1–2 locally already proves managed-identity-style auth works with no API keys
anywhere — the same code path picks up an App Service managed identity automatically
once that hosting is added in a later amendment, with `principalId` simply pointed at
the new identity instead of yours.
</content>
