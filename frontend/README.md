# Frontend — RAG Document Q&A Application

React 18 + TypeScript + Vite + React Router. Talks to the FastAPI backend over
`/api/v1` (see `vite.config.ts`'s dev-server proxy). See
[`../specs/001-rag-document-qa/quickstart.md`](../specs/001-rag-document-qa/quickstart.md)
for end-to-end manual validation scenarios (register/login, upload → ask → cited
answer, history, admin eval/metrics).

## Local setup

Prerequisites: Node 20 LTS, and the backend running at `http://127.0.0.1:8000`
(see [`../backend/README.md`](../backend/README.md) — it needs its own `az login`
for Azure access; the frontend itself has no Azure dependency).

```bash
npm install
npm run dev      # Vite dev server, proxying /api to the backend
npm run build    # tsc -b && vite build
npm run test     # Vitest + React Testing Library
npm run lint     # ESLint
npm run format   # Prettier --check
```

Or, from the repo root: `make install_frontend`, `make run_frontend`. Dev server
listens on `http://localhost:5173`. If port 8000 is unavailable, override the
proxy target locally without touching the committed default: `BACKEND_PORT=8001
npm run dev` (and start the backend on the matching port).

## Testing

```bash
npm run test      # Vitest + React Testing Library
npm run lint       # eslint
npm run format     # prettier --check
npm run build      # tsc -b && vite build
```

Or from the repo root: `make test_frontend`, `make lint_frontend`.

Tests mock the service layer (`src/features/*/*.ts`, e.g. `documents.ts`,
`queries.ts`) rather than hitting a real backend — see `tests/features/**/*.test.tsx`
for the pattern (render with a mocked service call, assert on rendered output /
calls made).

## Design system

Styling is Tailwind CSS (`tailwind.config.ts`) plus a small set of
hand-authored [shadcn/ui](https://ui.shadcn.com) primitives in
`src/components/ui/` (button, input, textarea, label, card, alert, badge,
avatar, skeleton, separator, dialog, table) — this is the **only** place a
styled primitive is defined; feature code composes these rather than
hand-rolling its own styled elements.

- **Color palette**: semantic CSS-variable tokens defined once in
  `src/index.css` (`background`, `foreground`, `primary`, `secondary`,
  `muted`, `accent`, `destructive`, `border`, `input`, `ring`), plus a
  dedicated `citation`/`citation-foreground` pair so a citation is always
  visually distinct from the answer text it supports.
- **Spacing**: Tailwind's default 4px-based scale, used directly — no
  one-off pixel values in component code.
- **Typography**: page titles (`text-2xl font-semibold`), section/card
  headings (`text-lg`), body text (`text-sm`), secondary/meta text
  (`text-xs text-muted-foreground`).
- **`cn()`** (`src/lib/utils.ts`) merges Tailwind classes via `clsx` +
  `tailwind-merge`, the standard shadcn/ui convention.

Every screen shows a loading indicator while a request is pending, a
distinct empty-state message when there's nothing to show, and a styled
(never raw-JSON) error message on failure. The app is responsive down to a
375px-wide viewport with no required horizontal scrolling.

## Structure

`src/` is organized by feature, mirroring the backend's `api/`→`services/`
split, rather than by technical layer:

```text
src/
├── components/ui/     # shadcn/ui primitives — the only shared styled elements
├── lib/utils.ts        # cn() class-merge helper
├── features/
│   ├── auth/            # login/register forms + pages, auth context, JWT client
│   ├── upload/           # document upload + list (loading/empty/error states)
│   ├── query/             # POST /queries client, shared Answer/Citation types,
│   │                      #   CitationBadge (shared between chat and history)
│   ├── chat/               # the live Q&A screen: a scrolling chat conversation
│   │                      #   (useConversation, ChatWindow, ChatBubble,
│   │                      #   TypingIndicator, ChatInput, ChatPage)
│   ├── history/             # past-query browsing (separate from the live chat)
│   └── admin/                # evaluation + operational-metrics screens
├── App.tsx                    # route wiring
└── main.tsx
```

## Routes

| Path                  | Who                                          | Page                                                  |
| --------------------- | -------------------------------------------- | ----------------------------------------------------- |
| `/login`, `/register` | anyone (redirects away if already logged in) | `LoginPage`, `RegisterPage`                           |
| `/`                   | any authenticated user                       | `ChatPage` (upload + conversational Q&A)              |
| `/history`            | any authenticated user                       | `HistoryPage`                                         |
| `/admin/eval`         | admin/evaluator role only                    | `AdminEvalPage` (benchmark dataset + comparison runs) |
| `/admin/metrics`      | admin/evaluator role only                    | `AdminMetricsPage` (operational health)               |

`isAdmin` (decoded client-side from the JWT, in `src/features/auth/auth.ts`) gates
the two admin routes and their nav links — the backend independently enforces
`require_admin` on every admin route regardless, so this is a UX convenience, not
the actual security boundary.

## The chat conversation

The live question/answer screen (`features/chat/`) holds its message list
as client-side-only state (`useConversation`) — an array of
`{ id, role, content, citations?, timestamp, status }` view models, not a
new persisted entity (the authoritative record is still the
`Query`/`Answer`/`Citation` rows the backend already stores, browsable via
History). Submitting a question appends the user's message and a pending
assistant placeholder immediately; the placeholder renders an animated
typing indicator until `POST /queries` resolves, then updates in place to
the complete, cited answer or a styled error bubble.

The backend's `/queries` endpoint returns one JSON response, not a
token stream, so this iteration doesn't stream partial output — the typing
indicator stays visible for the full wait and the answer renders all at
once. See `specs/001-rag-document-qa/research.md` for the full rationale.

Clicking a citation opens a dialog with the exact passage it was grounded in;
clicking a `ready` document in the sidebar opens a dialog listing everything
that document was indexed as (`GET /documents/{id}/passages`) — no raw file
bytes are ever stored or served, only extracted passage text.

## No App Service yet

There's no hosted deployment of either app in this iteration — both run locally
against real (or, for tests, mocked) Azure resources. See the backend README's
"Azure / no App Service yet" section for what changes once hosting is added.
