# Frontend — RAG Document Q&A Application

React 18 + TypeScript, built with Vite. Talks to the FastAPI backend over
`/api/v1` (see `vite.config.ts`'s dev-server proxy to `http://localhost:8000`).

## Local setup

```bash
npm install
npm run dev      # Vite dev server, proxying /api to the backend
npm run build    # tsc -b && vite build
npm run test     # Vitest + React Testing Library
npm run lint     # ESLint
npm run format   # Prettier --check
```

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
