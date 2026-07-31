# Feature Specification: RAG Document Q&A Application

**Feature Branch**: `001-rag-document-qa`

**Created**: 2026-07-30

**Status**: Draft

**Input**: User description: "Build a RAG (retrieval-augmented generation) application that lets a user upload documents or ask questions about previously uploaded content. The system should retrieve relevant source material for a given question, generate an answer grounded in that material, and include citations back to the specific source documents used. Responses must be returned in a validated, structured format, not free text. Results should be saved so a user can revisit past queries and answers. The system must handle errors gracefully (upload failures, retrieval failures, generation failures) with clear, non-leaking error messages. Separately, the system's behavior must be measurable: define what a \"correct,\" \"relevant,\" and \"grounded\" (non-hallucinated) response looks like, maintain a dataset of example questions with expected answers, and support comparing two versions of the system against that dataset to determine which performs better. The system must also track operational health in production: response latency, token consumption, and error rates." Amendment: "The system is multi-user — each user has their own account and can only see their own uploaded documents, saved queries, and results. Users must be able to register and log in using either their email or username, plus a password." Amendment (visual design): "The frontend currently has no visual design and must have a coherent, professional look applied consistently across every screen, with clear visual feedback for loading, empty, and error states, citations visually distinguished from answer text, and a layout usable on both desktop and mobile widths. The question-and-answer screen must be redesigned as a chatbot-style conversation — scrolling message bubbles distinguishing the user's questions from the system's answers, with a typing/thinking indicator while a response is generating — replacing the current static request/response layout."

## Clarifications

### Session 2026-07-30

- Q: What response-time target should the core question-answering loop (from a submitted question to a returned cited answer) meet? → A: ~15 seconds — allows more thorough retrieval/generation, appropriate for a deep-research-style tool rather than instant chat.
- Q: Who should be able to run version comparisons and view production operational health metrics? → A: Restricted to a dedicated administrator/evaluator role, distinct from regular end-user accounts.
- Q: Should the system enforce per-user limits on uploads or questions to contain cost and abuse? → A: Yes, on both document uploads and questions asked.
- Q: Can a user delete a document they previously uploaded, and what happens to past answers that cited it? → A: Deletion is allowed; past answers/citations that referenced the document remain in history, marked as referencing a removed source.

### Session 2026-07-30 (post-plan follow-up)

- Q: What is the maximum size allowed for a single uploaded document? → A: 10 MB per file.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and Log In to a Personal Account (Priority: P1)

A new visitor creates an account by providing a unique email address, a unique
username, and a password. A returning user logs in using either their email or their
username, plus their password, and is taken to a workspace containing only their own
uploaded documents, queries, and answers.

**Why this priority**: Every other capability — uploading documents, asking questions,
viewing history — depends on knowing which account a piece of data belongs to. Without
registration and login, per-user data isolation (a hard security requirement) cannot
exist, making this foundational alongside the core Q&A loop.

**Independent Test**: Can be fully tested by registering a new account, logging out,
then logging back in once with the registered email and once with the registered
username (same password), and confirming both succeed and an incorrect password is
rejected.

**Acceptance Scenarios**:

1. **Given** a new visitor with no account, **When** they register with a unique
   email, a unique username, and a password, **Then** the account is created and they
   can subsequently log in with those credentials.
2. **Given** a registered user, **When** they log in with their registered email and
   correct password, **Then** they are authenticated into a workspace containing only
   their own documents, queries, and answers.
3. **Given** a registered user, **When** they log in with their registered username and
   correct password, **Then** they are authenticated the same as when logging in with
   their email.
4. **Given** a visitor attempts to register with an email or username already in use,
   **When** they submit the registration, **Then** the system rejects it with a clear
   error message identifying the conflict, without exposing any other account's
   details.
5. **Given** a registered user enters an incorrect password or an unrecognized email or
   username, **When** they attempt to log in, **Then** the system rejects the attempt
   with a generic error message that does not reveal whether the identifier or the
   password was the one that was wrong.

---

### User Story 2 - Ask Grounded, Cited Questions Over Uploaded Documents (Priority: P1)

A logged-in user uploads one or more documents, then asks a question in natural
language. The system finds the passages relevant to the question, generates an answer
based only on those passages, and returns the answer together with citations pointing
to the specific source document(s) and location(s) the answer was drawn from — all in a
structured format the user's client can reliably parse and display.

**Why this priority**: This is the core value of the product. Without a working
upload-then-ask loop that produces a grounded, cited, structured answer, there is no
product — every other capability (accounts, history, evaluation, monitoring) exists to
support, secure, or measure this loop.

**Independent Test**: Can be fully tested by uploading a small set of documents,
asking a question whose answer is contained in them, and verifying the response
(a) is valid against the defined structured schema, (b) contains an answer, and
(c) cites the specific document(s) the answer came from.

**Acceptance Scenarios**:

1. **Given** a user has successfully uploaded a document, **When** they ask a question
   whose answer is contained in that document, **Then** the system returns a
   structured response containing an answer and at least one citation identifying the
   source document (and the passage/location within it) that supports the answer.
2. **Given** a user has uploaded multiple documents, **When** they ask a question whose
   answer draws on passages from more than one document, **Then** the response cites
   every document actually used to support the answer.
3. **Given** a user asks a question with no answer contained in any of their uploaded
   documents, **When** the system processes the question, **Then** the response
   explicitly indicates that no grounded answer was found rather than fabricating one.
4. **Given** a user submits a question with no documents uploaded yet, **When** the
   system processes the question, **Then** the response clearly states that there is no
   content to search rather than returning an empty or misleading answer.
5. **Given** a user deletes a document they previously uploaded, **When** they later
   view a past answer that cited that document, **Then** the answer and citation
   remain visible in history, marked as referencing a removed source, rather than
   being deleted or shown as broken.

---

### User Story 3 - Revisit Past Queries and Answers (Priority: P2)

A user who has previously asked questions can return to the system and browse or
retrieve the exact questions they asked, the answers they received, and the citations
that came with those answers, without having to re-ask.

**Why this priority**: Saved history turns single-use answers into a reusable
knowledge trail and is explicitly required, but it depends on Story 2 already producing
saved, structured results — so it is the next layer of value rather than the
foundation.

**Independent Test**: Can be fully tested by asking a question, confirming the
resulting query/answer/citation record appears in the user's history, and confirming
it can be retrieved later in the same structured form it was originally returned in.

**Acceptance Scenarios**:

1. **Given** a user has asked one or more questions in the past, **When** they open
   their query history, **Then** they see each past question along with its answer and
   citations, ordered by most recent first.
2. **Given** a user selects a specific past query, **When** the system displays it,
   **Then** the displayed answer and citations exactly match what was originally
   returned at the time the question was asked.
3. **Given** a user has never asked a question, **When** they open their query
   history, **Then** the system shows a clear empty-state message rather than an error.

---

### User Story 4 - Compare Two System Versions Against a Benchmark Dataset (Priority: P2)

An account with the administrator/evaluator role maintains a dataset of example
questions with expected answers, runs both a current and a candidate version of the
system against that dataset, and receives a comparison showing which version performs
better against defined correctness, relevance, and groundedness criteria. Regular
end-user accounts cannot access this capability.

**Why this priority**: The request explicitly separates "measurability" from the
end-user experience — this capability is what allows the team to know whether a change
made the system better or worse before it reaches users. It is essential to safe
iteration but is not part of the end-user's direct journey, so it ranks alongside
history rather than above the core Q&A loop.

**Independent Test**: Can be fully tested by running two versions of the system against
a small fixed dataset of question/expected-answer pairs and confirming the system
produces a per-question and aggregate scored comparison identifying the better-performing
version.

**Acceptance Scenarios**:

1. **Given** a dataset of example questions with expected answers, **When** an
   evaluator runs a comparison between two named system versions, **Then** the system
   scores every dataset question for both versions against correctness, relevance, and
   groundedness, and reports an aggregate result per version.
2. **Given** a completed comparison run, **When** the evaluator views the results,
   **Then** the system clearly indicates which version scored better overall and shows
   the per-question scores that informed that result.
3. **Given** one version fails to produce any response for a dataset question during a
   comparison run, **When** scoring completes, **Then** that question is recorded as a
   failure for that version rather than silently excluded from the results.
4. **Given** a regular end-user account (not administrator/evaluator), **When** it
   attempts to start a comparison run or view comparison results, **Then** the system
   rejects the attempt as not authorized.

---

### User Story 5 - Monitor Operational Health in Production (Priority: P3)

An account with the administrator/evaluator role can observe, for the running system,
how long responses take, how many tokens are being consumed, and how often requests
are failing, in order to detect degradation or cost issues before they significantly
affect users. Regular end-user accounts cannot access this capability.

**Why this priority**: Operational visibility is necessary for running the system
responsibly in production but does not change what value an end user receives from any
single interaction, so it is the lowest priority — valuable but not blocking initial
delivery of user-facing value.

**Independent Test**: Can be fully tested by generating a mix of successful and failing
requests and confirming that latency, token consumption, and error rate are all
recorded and retrievable as observable metrics reflecting that traffic.

**Acceptance Scenarios**:

1. **Given** the system is processing question and upload requests, **When** an
   operator inspects operational metrics, **Then** they can see response latency,
   token consumption, and error rate for a given recent time window.
2. **Given** a spike in failed requests occurs, **When** an operator inspects error
   rate metrics, **Then** the increase is visible and attributable to a request type
   (upload, retrieval, or generation).
3. **Given** a regular end-user account (not administrator/evaluator), **When** it
   attempts to view operational health metrics, **Then** the system rejects the
   attempt as not authorized.

---

### User Story 6 - Experience a Polished, Conversational Q&A Interface (Priority: P2)

Every screen a user encounters — registering, logging in, uploading documents, asking
questions, reviewing results, and browsing history — presents a single, coherent visual
design rather than unstyled or inconsistent pages, and clearly communicates what is
happening at every moment (loading, empty, or error) without ever showing raw technical
output. Asking questions and receiving answers happens in a conversational interface:
the user's own questions and the system's answers appear as a scrolling sequence of
visually distinct messages, with a visible "thinking" indicator while an answer is being
generated, rather than a static one-question-at-a-time form.

**Why this priority**: The underlying capabilities (accounts, grounded Q&A, history)
already work by the time this story is addressed — this story is about making that
value legible, trustworthy, and pleasant to use, which matters for real adoption but
does not gate any of the functionality it presents. It ranks alongside history and
evaluation rather than above the core Q&A loop itself.

**Independent Test**: Can be fully tested by navigating every screen and confirming a
single consistent visual style; by triggering a slow upload/question, an empty
documents/history list, and a failed request and confirming each shows its own clearly
styled state (loading, empty, error) with no raw/unstyled technical output visible; and
by asking a question and confirming it appears as a distinct user message immediately,
followed by a visible thinking indicator, then a distinct answer message, all in a
scrolling conversation view that remains usable at both a typical desktop and a typical
mobile viewport width.

**Acceptance Scenarios**:

1. **Given** a user moves between the login, registration, upload, question/answer, and
   history screens, **When** they view each screen, **Then** all screens share the same
   typography, spacing, and color scheme rather than looking like disconnected pages.
2. **Given** a user submits a question or uploads a document, **When** the request is
   still being processed, **Then** the system shows a visible loading/progress
   indicator rather than an unresponsive or blank screen.
3. **Given** a user has no uploaded documents or no past questions yet, **When** they
   view the relevant screen, **Then** the system shows a distinct, clearly worded empty
   state rather than a blank area or an error.
4. **Given** a request fails for any reason, **When** the failure is shown to the user,
   **Then** it appears as a clearly styled, human-readable message rather than raw or
   unstyled technical output (e.g., raw JSON).
5. **Given** an answer includes one or more citations, **When** the user views it,
   **Then** the citations are visually distinguishable from the main answer text they
   support.
6. **Given** a user asks a question, **When** the answer is being generated, **Then**
   their question immediately appears as its own message in a scrolling conversation,
   a visible "thinking" indicator appears while the answer is generated, and the
   indicator is replaced by the answer as its own, visually distinct message once ready.
7. **Given** a user views the application on a narrow (mobile-width) screen instead of a
   desktop-width screen, **When** they use any screen, **Then** all content and controls
   remain usable without being cut off or requiring horizontal scrolling to reach.

---

### Edge Cases

- What happens when a registration attempt reuses an email or username already
  associated with an existing account? The system MUST reject it with a clear,
  specific error identifying the conflicting field, without leaking any other
  account's details.
- What happens when a user tries to access another user's document, query, or answer
  directly (e.g., by guessing an identifier)? The system MUST treat it as not
  found/not authorized rather than revealing that the resource exists under a
  different account.
- What happens when a user uploads a file that is empty, corrupted, password-protected,
  in an unsupported format, or larger than the 10 MB per-file limit? The system MUST
  reject it with a clear, specific, non-leaking error message rather than a generic
  failure or a successful-looking upload of unusable content.
- What happens when the retrieval step finds no relevant material for a question? The
  system MUST say so in the structured response rather than passing empty context to
  answer generation and risking a fabricated answer.
- What happens when answer generation itself fails or times out after retrieval
  succeeded? The system MUST return a structured error response (not a partial or
  malformed answer) and MUST NOT expose internal error details (e.g., stack traces,
  provider error payloads, infrastructure identifiers) to the user.
- What happens when a user's own documents contain conflicting information relevant to
  the same question? The system's answer and citations should reflect what is actually
  in the retrieved source material, allowing the user to see the conflict via the cited
  passages rather than the system silently picking one side.
- What happens when a benchmark comparison run is interrupted partway through (e.g.,
  one version becomes unavailable mid-run)? The comparison MUST report which questions
  were scored and which were not, rather than presenting an incomplete run as a
  complete one.
- What happens when token consumption or latency for a single request is abnormally
  high? This MUST still be captured in operational metrics rather than being dropped as
  an outlier.
- What happens when a user exceeds their upload or question rate limit? The system
  MUST reject the request with a clear, specific error indicating the limit and when
  it resets, rather than a generic failure or silent throttling.
- What happens when a user deletes a document that is cited by one or more past
  answers? The document MUST stop being available for future retrieval, but existing
  answers and citations that referenced it MUST remain visible in history, marked as
  referencing a removed source.
- What happens when an answer takes close to the maximum expected time to generate?
  The "thinking" indicator MUST remain visible for the entire wait rather than
  disappearing prematurely or appearing frozen, so the user can tell the system is
  still working rather than stuck.
- What happens when an answer or its citations are long relative to a narrow
  (mobile-width) screen? The content MUST wrap and scroll within its own message
  rather than being clipped, overflowing the screen, or breaking the surrounding layout.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a new user to register an account by providing a
  unique email address, a unique username, and a password.
- **FR-002**: System MUST allow a registered user to log in by providing either their
  registered email address or their registered username, together with their password.
- **FR-003**: System MUST reject registration attempts that reuse an email address or
  username already associated with an existing account, returning a clear error
  message that identifies the conflicting field without revealing any other account's
  details.
- **FR-004**: System MUST reject login attempts with an incorrect password or an
  unrecognized email/username using a single generic error message that does not
  reveal which of the two was incorrect.
- **FR-005**: System MUST enforce a minimum password strength (at least 8 characters)
  at registration.
- **FR-006**: System MUST scope every uploaded document, submitted query, generated
  answer, and history entry to the account that created it, and MUST prevent any other
  account from viewing, retrieving, or citing another account's documents, queries, or
  answers.
- **FR-007**: System MUST restrict initiating comparison runs (User Story 4) and
  viewing operational health metrics (User Story 5) to accounts with an
  administrator/evaluator role; regular user accounts MUST NOT be able to access
  either capability.
- **FR-008**: System MUST allow an authenticated user to upload documents in common
  text-based formats (PDF, Word `.docx`, plain text `.txt`, and Markdown) for later
  question answering.
- **FR-009**: System MUST reject uploads that are empty, unreadable/corrupted,
  password-protected, not in a supported format, or larger than 10 MB, returning a
  clear, specific, non-leaking error message that names the problem without exposing
  internal system details.
- **FR-010**: System MUST allow a user to delete a document they previously uploaded;
  once deleted, the document MUST no longer be available for retrieval, but any
  existing answer or citation that referenced it MUST remain in the user's history,
  marked as referencing a removed source.
- **FR-011**: System MUST allow an authenticated user to submit a natural-language
  question to be answered using only their own previously uploaded documents.
- **FR-012**: System MUST enforce a per-user limit on the number of documents uploaded
  and questions asked within a rolling time period, rejecting requests that exceed the
  limit with a clear error indicating the limit and when it resets.
- **FR-013**: System MUST retrieve the source material relevant to a submitted question
  before generating an answer.
- **FR-014**: System MUST generate an answer that is grounded in the retrieved source
  material and MUST NOT present claims that are not supported by that material as
  though they were.
- **FR-015**: System MUST return every answer together with citations that identify the
  specific source document(s) and location(s) (e.g., page, section, or passage) that
  support the answer; an answer with unsupported claims MUST NOT be presented as fully
  cited.
- **FR-016**: System MUST return every question response (successful, no-answer-found,
  or error) in a validated, structured format conforming to a defined schema, never as
  unstructured free text.
- **FR-017**: System MUST explicitly indicate in the structured response when no
  grounded answer could be found, rather than fabricating a plausible-sounding answer.
- **FR-018**: System MUST persist every submitted question, its structured answer, and
  its citations, associated with the user who asked it.
- **FR-019**: System MUST allow a user to retrieve and browse their own past questions,
  answers, and citations, ordered most-recent-first, and MUST return an explicit
  empty-state result for a user with no history rather than an error.
- **FR-020**: System MUST return the exact previously generated answer and citations
  when a user revisits a past query, rather than re-running generation.
- **FR-021**: System MUST classify failures by stage (upload, retrieval, or generation)
  and return a structured, user-facing error response for each that describes the
  problem in general terms without leaking internal implementation details (e.g., no
  stack traces, credentials, infrastructure hostnames, or raw third-party error
  payloads).
- **FR-022**: System MUST define explicit, documented criteria for what counts as a
  "correct" response (the answer matches the expected answer's meaning), a "relevant"
  response (the answer addresses what was actually asked), and a "grounded" response
  (every claim in the answer is supported by retrieved source material, with no
  unsupported/hallucinated claims).
- **FR-023**: System MUST maintain a benchmark dataset of example questions paired with
  their expected answers, usable for repeatable evaluation.
- **FR-024**: System MUST support running two named versions of the system against the
  benchmark dataset and automatically scoring each version's responses against the
  correctness, relevance, and groundedness criteria (FR-022) without requiring manual
  human grading of individual responses.
- **FR-025**: System MUST report, per comparison run, a per-question score and an
  aggregate score for each version, and MUST indicate which version performed better
  overall.
- **FR-026**: System MUST record a dataset question as a failure for a given version
  when that version fails to produce a response during a comparison run, rather than
  omitting it from the results.
- **FR-027**: System MUST record, for every production request, its latency, its token
  consumption, and whether it succeeded or failed (and at which stage), so that these
  can be observed as operational metrics.
- **FR-028**: System MUST make latency, token consumption, and error-rate metrics
  observable for a given recent time window, broken down by request stage (upload,
  retrieval, generation).
- **FR-029**: System MUST present a single, coherent visual design — consistent
  typography, spacing, and color scheme — across every screen (login, register,
  upload, question/answer, history).
- **FR-030**: System MUST show a visible loading/progress indicator while a document
  upload or question submission is being processed, MUST show a distinct empty-state
  message when no documents or history entries exist, and MUST present every failure
  as a clearly styled, human-readable message rather than raw or unstyled technical
  output (e.g., raw JSON).
- **FR-031**: System MUST visually distinguish an answer's citations from the main
  answer text they support.
- **FR-032**: System MUST remain fully usable, with no content or controls cut off or
  requiring horizontal scrolling to reach, at both desktop and mobile (narrow) viewport
  widths.
- **FR-033**: System MUST present the question-and-answer interaction as a
  chronological, scrolling sequence of messages, with the user's own questions and the
  system's answers rendered as visually distinct message types, rather than a static
  one-question-at-a-time layout.
- **FR-034**: System MUST show a visible "thinking" indicator within the conversation
  while an answer is being generated, replacing it with the completed answer message
  (or, per FR-030, a styled error message) once generation finishes.

### Key Entities

- **User Account**: A registered user of the system. Key attributes: unique
  identifier, email address (unique), username (unique), password (stored securely,
  never in plain text), role (standard user or administrator/evaluator), account
  creation timestamp.
- **Document**: A file uploaded by a user to be used as source material. Key
  attributes: owning User Account, original filename, format, upload status
  (processing/ready/failed/deleted), failure reason (if any), upload timestamp. A
  deleted Document is excluded from future retrieval but is retained for existing
  Citation history.
- **Source Passage**: A retrievable unit of content extracted from a Document (e.g., a
  chunk, page, or section). Key attributes: parent Document reference, location/position
  within the Document, text content.
- **Query**: A question submitted by a user. Key attributes: owning User Account,
  question text, submission timestamp, status (answered/no-answer-found/failed).
- **Answer**: The structured, validated response produced for a Query. Key attributes:
  parent Query reference, answer content, list of Citations, groundedness status,
  generation timestamp.
- **Citation**: A pointer from an Answer back to the specific Source Passage(s) (and
  therefore Document(s)) that support it. Key attributes: reference to the Source
  Passage/Document, a flag indicating whether the underlying Document has since been
  deleted.
- **Evaluation Dataset Item**: An example question paired with its expected answer,
  used for repeatable benchmarking. Key attributes: question text, expected answer,
  optional expected supporting source reference.
- **Comparison Run**: A single execution of two named system versions against the
  Evaluation Dataset. Key attributes: the two version identifiers, per-question scores
  (correctness, relevance, groundedness) for each version, aggregate scores, overall
  result, run timestamp.
- **Operational Metric Record**: A recorded measurement of a production request. Key
  attributes: request stage (upload/retrieval/generation), latency, token consumption,
  success/failure status, timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new visitor can register an account and log back in successfully using
  either their email or their username in under 2 minutes without help or
  documentation.
- **SC-002**: A user can go from uploading a document to receiving a grounded, cited
  answer about its contents in a single session without needing help or documentation.
- **SC-003**: At least 95% of question responses conform to the defined structured
  response format with zero unstructured free-text responses reaching the user.
- **SC-004**: 100% of answers that make a factual claim include at least one citation
  to source material; 0% of answers present unsupported claims as grounded fact.
- **SC-005**: Users can locate and correctly re-view any past question and its original
  answer in under 10 seconds of browsing their history.
- **SC-006**: 100% of upload, retrieval, and generation failures are surfaced to the
  user as a clear, specific error message, with 0% of error messages exposing internal
  system details.
- **SC-007**: 0% of attempts by one user to view, retrieve, or cite another user's
  documents, queries, or answers succeed.
- **SC-008**: A benchmark comparison between two system versions completes and
  produces a clear better/worse determination for at least 95% of dataset questions
  without manual grading effort.
- **SC-009**: Operators can determine current response latency, token consumption, and
  error rate for the production system at any time, with data no more than 5 minutes
  stale.
- **SC-010**: A degradation in error rate or latency for a specific request stage
  (upload, retrieval, or generation) is identifiable from operational metrics within 5
  minutes of it starting.
- **SC-011**: At least 95% of question responses are returned within 15 seconds of
  submission.
- **SC-012**: 100% of requests that exceed a user's upload or question rate limit are
  rejected with a clear, specific error rather than being processed.
- **SC-013**: 100% of screens (login, register, upload, question/answer, history) use
  the same typography, spacing, and color scheme, with zero screens presenting an
  unstyled or visually inconsistent one-off appearance.
- **SC-014**: 100% of loading, empty, and error states are shown with a distinct,
  clearly styled indicator or message; 0% of failed requests display raw or unstyled
  technical output (e.g., raw JSON) to the user.
- **SC-015**: A new user can, without explanation, correctly tell their own questions
  apart from the system's answers in the conversation view, and can identify when the
  system is still generating a response versus when it has finished.
- **SC-016**: The application remains fully usable — no cut-off content, no required
  horizontal scrolling of primary content — at both a typical desktop viewport width
  (e.g., 1280px) and a typical mobile viewport width (e.g., 375px).

## Assumptions

- The system is multi-user: each account's documents, queries, and answers are private
  to that account and are never visible to other accounts (confirmed).
- Registration collects both a unique email address and a unique username per account;
  login accepts either identifier together with the password (confirmed).
- Password reset/account-recovery flows and multi-factor authentication are out of
  scope for this version; the underlying session/token mechanism used to keep a user
  logged in (e.g., cookies vs. bearer tokens) is an implementation detail left to the
  planning phase.
- "Correct," "relevant," and "grounded" are scored using automated grading (e.g., a
  model-based judge and/or rule-based checks) against the benchmark dataset, with no
  manual human review required for a comparison run to complete (confirmed).
- Supported upload formats for this version are common text-based documents: PDF,
  Word (`.docx`), plain text (`.txt`), and Markdown; scanned/image-based documents
  requiring OCR and other formats (spreadsheets, presentations, HTML) are out of scope
  for this version (confirmed).
- Benchmark comparison runs are initiated on demand by an account with the
  administrator/evaluator role rather than continuously in the background; this role
  is provisioned out-of-band (e.g., by a system operator) rather than through
  self-service registration in this version.
- Default per-user rate limits are 50 document uploads and 200 questions per rolling
  24-hour period; exact thresholds are configurable and may be refined during
  planning.
- The maximum size for a single uploaded document is 10 MB (confirmed).
- Data retention for uploaded documents, query history, and operational metrics follows
  standard industry practice (retained until the user deletes it or an administrator
  purges it); no specific regulatory retention period was indicated.
- The conversational message view (User Story 6) is a redesign of how the live
  question/answer screen presents the current session's back-and-forth; it does not
  change the separate History feature (User Story 3) or its underlying data — a user's
  past questions and answers are still requested, structured, and revisited exactly as
  User Story 3 already defines. The two remain distinct screens, matching the request's
  own listing of "query" and "results/history" as separate screens.
- "Usable on mobile widths" means a responsive web layout (the same web application
  adapting to a narrower viewport), not a separate native mobile app.
- The specific visual design choices (exact color palette, font family, spacing scale,
  component styling) are implementation details left to the planning phase; this
  specification requires that a single design be applied consistently, not any
  particular look.
- Admin-only screens (comparison-run dataset/results, operational metrics) are covered
  by the same consistent visual design and responsive-layout requirements as the
  end-user screens; the conversational message redesign (FR-033, FR-034) applies only to
  the end-user question/answer screen, since the admin screens are not conversational
  in nature.
</content>
