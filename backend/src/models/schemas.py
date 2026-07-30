"""Pydantic request/response schemas.

Populated incrementally per user story: the shared Error schema here
(Foundational); auth schemas in User Story 1; document/query/answer/
citation schemas in User Story 2; eval schemas in User Story 4.
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Error(BaseModel):
    """Clear, user-facing, non-leaking error message (FR-021).

    Never contains stack traces, credentials, infrastructure hostnames, or
    raw third-party error payloads.
    """

    detail: str


# --- User Story 1: Register and Log In -------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, description="Either the account's email or username.")
    password: str = Field(min_length=1)


class AuthToken(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
