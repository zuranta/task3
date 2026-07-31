"""The admin-provisioning script produces an account whose role is admin, and
that account passes the /admin/eval/* authz checks (/speckit-analyze finding U3).
"""

import pytest

from scripts.create_admin import create_or_promote_admin
from src.core.security import create_access_token
from src.services import eval_service


@pytest.mark.asyncio
async def test_create_admin_creates_a_new_admin_account_that_passes_authz(client, monkeypatch):
    monkeypatch.setattr(eval_service.dataset_sync, "list_dataset_items", lambda: [])

    user = await create_or_promote_admin(
        identifier="newadmin@example.com",
        email="newadmin@example.com",
        username="newadmin",
        password="correcthorse",
    )
    assert user.role.value == "admin"

    token = create_access_token(user_id=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/eval/dataset-items", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_admin_promotes_an_existing_user(register_user):
    _, user_id = await register_user("promoteme")

    user = await create_or_promote_admin(identifier="promoteme")

    assert user.id == user_id
    assert user.role.value == "admin"


@pytest.mark.asyncio
async def test_create_admin_requires_details_for_a_brand_new_account():
    with pytest.raises(ValueError):
        await create_or_promote_admin(identifier="nobody-matches-this@example.com")
