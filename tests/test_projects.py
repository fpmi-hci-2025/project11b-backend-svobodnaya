"""Tests for project endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCreateProject:
    """Tests for POST /api/projects"""

    async def test_create_project_success(self, client: AsyncClient, auth_headers):
        """Test successful project creation."""
        response = await client.post(
            "/api/projects",
            json={"name": "New Project", "description": "Project description"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "Project description"
        assert "id" in data
        assert "owner" in data
        assert data["owner"]["username"] == "testuser"

    async def test_create_project_minimal(self, client: AsyncClient, auth_headers):
        """Test creating project with only name."""
        response = await client.post(
            "/api/projects",
            json={"name": "Minimal Project"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["description"] is None

    async def test_create_project_unauthorized(self, client: AsyncClient):
        """Test creating project without authentication."""
        response = await client.post(
            "/api/projects",
            json={"name": "Project"},
        )
        assert response.status_code == 401

    async def test_create_project_empty_name(self, client: AsyncClient, auth_headers):
        """Test creating project with empty name."""
        response = await client.post(
            "/api/projects",
            json={"name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetProjects:
    """Tests for GET /api/projects"""

    async def test_get_projects_empty(self, client: AsyncClient, auth_headers):
        """Test getting projects when user has none."""
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_projects_owned(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test getting owned projects."""
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project"

    async def test_get_projects_as_member(
        self, client: AsyncClient, auth_headers_user2, test_project_with_member
    ):
        """Test getting projects where user is member."""
        response = await client.get("/api/projects", headers=auth_headers_user2)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Project with Member"

    async def test_get_projects_unauthorized(self, client: AsyncClient):
        """Test getting projects without authentication."""
        response = await client.get("/api/projects")
        assert response.status_code == 401


class TestGetProject:
    """Tests for GET /api/projects/{project_id}"""

    async def test_get_project_owner(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test getting project as owner."""
        response = await client.get(
            f"/api/projects/{test_project.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["id"] == test_project.id

    async def test_get_project_member(
        self, client: AsyncClient, auth_headers_user2, test_project_with_member
    ):
        """Test getting project as member."""
        response = await client.get(
            f"/api/projects/{test_project_with_member.id}", headers=auth_headers_user2
        )
        assert response.status_code == 200

    async def test_get_project_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent project."""
        response = await client.get("/api/projects/99999", headers=auth_headers)
        assert response.status_code == 404

    async def test_get_project_no_access(
        self, client: AsyncClient, auth_headers_user2, test_project
    ):
        """Test getting project without access."""
        response = await client.get(
            f"/api/projects/{test_project.id}", headers=auth_headers_user2
        )
        assert response.status_code == 403


class TestUpdateProject:
    """Tests for PUT /api/projects/{project_id}"""

    async def test_update_project_owner(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test updating project as owner."""
        response = await client.put(
            f"/api/projects/{test_project.id}",
            json={"name": "Updated Name", "description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    async def test_update_project_partial(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test partial project update."""
        response = await client.put(
            f"/api/projects/{test_project.id}",
            json={"name": "Only Name Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Only Name Updated"

    async def test_update_project_member_forbidden(
        self, client: AsyncClient, auth_headers_user2, test_project_with_member
    ):
        """Test updating project as member (should fail)."""
        response = await client.put(
            f"/api/projects/{test_project_with_member.id}",
            json={"name": "Hacked Name"},
            headers=auth_headers_user2,
        )
        assert response.status_code == 403

    async def test_update_project_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent project."""
        response = await client.put(
            "/api/projects/99999",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteProject:
    """Tests for DELETE /api/projects/{project_id}"""

    async def test_delete_project_owner(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test deleting project as owner."""
        response = await client.delete(
            f"/api/projects/{test_project.id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify project is deleted
        response = await client.get(
            f"/api/projects/{test_project.id}", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_delete_project_member_forbidden(
        self, client: AsyncClient, auth_headers_user2, test_project_with_member
    ):
        """Test deleting project as member (should fail)."""
        response = await client.delete(
            f"/api/projects/{test_project_with_member.id}", headers=auth_headers_user2
        )
        assert response.status_code == 403

    async def test_delete_project_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent project."""
        response = await client.delete("/api/projects/99999", headers=auth_headers)
        assert response.status_code == 404


class TestProjectMembers:
    """Tests for project member management."""

    async def test_add_member_success(
        self, client: AsyncClient, auth_headers, test_project, test_user2
    ):
        """Test adding member to project."""
        response = await client.post(
            f"/api/projects/{test_project.id}/members",
            json={"user_id": test_user2.id},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["id"] == test_user2.id

    async def test_add_member_duplicate(
        self, client: AsyncClient, auth_headers, test_project_with_member, test_user2
    ):
        """Test adding already existing member."""
        response = await client.post(
            f"/api/projects/{test_project_with_member.id}/members",
            json={"user_id": test_user2.id},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already a member" in response.json()["detail"]

    async def test_add_owner_as_member(
        self, client: AsyncClient, auth_headers, test_project, test_user
    ):
        """Test adding owner as member (should fail)."""
        response = await client.post(
            f"/api/projects/{test_project.id}/members",
            json={"user_id": test_user.id},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Owner cannot be added" in response.json()["detail"]

    async def test_add_member_user_not_found(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test adding non-existent user as member."""
        response = await client.post(
            f"/api/projects/{test_project.id}/members",
            json={"user_id": 99999},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_add_member_not_owner(
        self, client: AsyncClient, auth_headers_user2, test_project_with_member, test_user3
    ):
        """Test adding member as non-owner (should fail)."""
        response = await client.post(
            f"/api/projects/{test_project_with_member.id}/members",
            json={"user_id": test_user3.id},
            headers=auth_headers_user2,
        )
        assert response.status_code == 403

    async def test_remove_member_success(
        self, client: AsyncClient, auth_headers, test_project_with_member, test_user2
    ):
        """Test removing member from project."""
        response = await client.delete(
            f"/api/projects/{test_project_with_member.id}/members/{test_user2.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_remove_member_not_found(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test removing non-existent member."""
        response = await client.delete(
            f"/api/projects/{test_project.id}/members/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_members_success(
        self, client: AsyncClient, auth_headers, test_project_with_member
    ):
        """Test getting project members."""
        response = await client.get(
            f"/api/projects/{test_project_with_member.id}/members",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user"]["username"] == "testuser2"

