# Frontend — RAG Document Q&A Application

React 18 + TypeScript + Vite + React Router. See
[`../specs/001-rag-document-qa/quickstart.md`](../specs/001-rag-document-qa/quickstart.md)
for end-to-end manual validation scenarios (register/login, upload → ask → cited
answer, history, admin eval/metrics).

## Local setup

Prerequisites: Node 20 LTS, and the backend running at `http://127.0.0.1:8000`
(see [`../backend/README.md`](../backend/README.md) — it needs its own `az login`
for Azure access; the frontend itself has no Azure dependency).

```bash
npm install
npm run dev
```

Or, from the repo root: `make install_frontend`, `make run_frontend`.

Dev server listens on `http://localhost:5173` and proxies API calls to the
backend (see `vite.config.ts`).

## Testing

```bash
npm run test      # Vitest + React Testing Library
npm run lint       # eslint
npm run format     # prettier --check
npm run build      # tsc -b && vite build
```

Or from the repo root: `make test_frontend`, `make lint_frontend`.

Component tests mock the service layer (`src/services/*`) rather than hitting a
real backend — see `tests/components/*.test.tsx` for the pattern (render with a
mocked service call, assert on rendered output / calls made).

## Routes

| Path | Who | Page |
|---|---|---|
| `/login`, `/register` | anyone (redirects away if already logged in) | `Login`, `Register` |
| `/` | any authenticated user | `Workspace` (upload + ask) |
| `/history` | any authenticated user | `History` |
| `/admin/eval` | admin/evaluator role only | `AdminEval` (benchmark dataset + comparison runs) |
| `/admin/metrics` | admin/evaluator role only | `AdminMetrics` (operational health) |

`isAdmin` (decoded client-side from the JWT, in `src/services/auth.ts`) gates the
two admin routes and their nav links — the backend independently enforces
`require_admin` on every admin route regardless, so this is a UX convenience, not
the actual security boundary.

## No App Service yet

There's no hosted deployment of either app in this iteration — both run locally
against real (or, for tests, mocked) Azure resources. See the backend README's
"Azure / no App Service yet" section for what changes once hosting is added.
