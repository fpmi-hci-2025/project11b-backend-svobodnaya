"""Tests for user endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestSearchUsers:
    """Tests for GET /api/users/search"""

    async def test_search_users_success(
        self, client: AsyncClient, auth_headers, test_user, test_user2
    ):
        """Test searching users."""
        response = await client.get(
            "/api/users/search?q=testuser", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        usernames = [u["username"] for u in data]
        assert "testuser" in usernames
        assert "testuser2" in usernames

    async def test_search_users_partial(
        self, client: AsyncClient, auth_headers, test_user
    ):
        """Test searching users with partial query."""
        response = await client.get("/api/users/search?q=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_search_users_case_insensitive(
        self, client: AsyncClient, auth_headers, test_user
    ):
        """Test case-insensitive search."""
        response = await client.get("/api/users/search?q=TESTUSER", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_search_users_no_results(
        self, client: AsyncClient, auth_headers
    ):
        """Test search with no results."""
        response = await client.get(
            "/api/users/search?q=nonexistentuser12345", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_search_users_empty_query(
        self, client: AsyncClient, auth_headers
    ):
        """Test search with empty query."""
        response = await client.get("/api/users/search?q=", headers=auth_headers)
        assert response.status_code == 422  # Validation error (min_length=1)

    async def test_search_users_unauthorized(self, client: AsyncClient):
        """Test search without authentication."""
        response = await client.get("/api/users/search?q=test")
        assert response.status_code == 401

    async def test_search_users_missing_query(
        self, client: AsyncClient, auth_headers
    ):
        """Test search without query parameter."""
        response = await client.get("/api/users/search", headers=auth_headers)
        assert response.status_code == 422

