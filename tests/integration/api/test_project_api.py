async def test_create_project_api(client, auth_token):
    """
    Test project creation via API.
    """
    response = await client.post(
        "/api/projects/",
        json={"name": "New Project", "description": "Desc"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert "id" in data


async def test_list_projects_api(client, auth_token):
    """
    Test listing projects via API.
    """
    # Create one
    await client.post(
        "/api/projects/",
        json={"name": "Project Alpha"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    response = await client.get(
        "/api/projects/", headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(p["name"] == "Project Alpha" for p in data)


async def test_unauthorized_access(client):
    response = await client.get("/api/projects/")
    assert response.status_code == 401


async def test_create_project_ignores_client_owner_id(client, auth_token, db_session):
    """
    Test that the API ignores an owner_id sent by the client and forces it
    to be the ID of the authenticated user (prevents ID spoofing).
    """
    from sqlalchemy import select

    from app.models.user import User

    # Create another user to try spoofing their ID
    other_user = User(
        email="other@example.com", hashed_password="pw", full_name="Other"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    spoofed_owner_id = other_user.id

    # Attempt to create a project with the spoofed owner_id
    response = await client.post(
        "/api/projects/",
        json={"name": "Spoof Attempt", "owner_id": spoofed_owner_id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    # Get current user ID
    res = await db_session.execute(
        select(User).where(User.email == "integration_user@example.com")
    )
    current_user = res.scalar_one()

    assert data["owner_id"] == current_user.id
    assert data["owner_id"] != spoofed_owner_id
