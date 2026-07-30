"""Pydantic request/response schemas.

Populated incrementally per user story: the shared Error schema here
(Foundational); auth schemas in User Story 1; document/query/answer/
citation schemas in User Story 2; eval schemas in User Story 4.
"""

from pydantic import BaseModel


class Error(BaseModel):
    """Clear, user-facing, non-leaking error message (FR-021).

    Never contains stack traces, credentials, infrastructure hostnames, or
    raw third-party error payloads.
    """

    detail: str
