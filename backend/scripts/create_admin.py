"""CLI to provision an administrator/evaluator account out-of-band (spec.md's
Assumptions; /speckit-analyze finding U3): promotes an existing user (by
email or username) to role=admin, or creates a new admin account directly if
no matching user exists. There is no in-app signup path to this role.
"""

import argparse
import asyncio

from sqlalchemy import or_, select

from src.core.db import _session_factory
from src.models.db import User, UserRole
from src.services.auth_service import hash_password


async def create_or_promote_admin(
    *,
    identifier: str,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> User:
    async with _session_factory() as db:
        result = await db.execute(
            select(User).where(or_(User.email == identifier, User.username == identifier))
        )
        user = result.scalar_one_or_none()

        if user is not None:
            user.role = UserRole.admin
        else:
            if email is None or username is None or password is None:
                raise ValueError(
                    "No existing user matches that identifier; --email, --username, "
                    "and --password are required to create a new admin account."
                )
            user = User(
                email=email,
                username=username,
                password_hash=hash_password(password),
                role=UserRole.admin,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)
        return user


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote an existing user to admin, or create a new admin account."
    )
    parser.add_argument("identifier", help="Existing user's email or username to promote.")
    parser.add_argument("--email", help="Email for a new account, if identifier doesn't match one.")
    parser.add_argument("--username", help="Username for a new account.")
    parser.add_argument("--password", help="Password for a new account.")
    args = parser.parse_args()

    user = asyncio.run(
        create_or_promote_admin(
            identifier=args.identifier,
            email=args.email,
            username=args.username,
            password=args.password,
        )
    )
    print(f"Account '{user.username}' ({user.email}) now has role={user.role.value}.")


if __name__ == "__main__":
    _main()
