"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestRegister:
    """Tests for POST /api/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration with already existing username."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"

    async def test_register_short_username(self, client: AsyncClient):
        """Test registration with too short username."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "ab", "password": "password123"},
        )
        assert response.status_code == 422  # Validation error

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with too short password."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "validuser", "password": "12345"},
        )
        assert response.status_code == 422  # Validation error

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing fields."""
        response = await client.post("/api/auth/register", json={})
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/auth/login"""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields."""
        response = await client.post("/api/auth/login", data={})
        assert response.status_code == 422


class TestMe:
    """Tests for GET /api/auth/me"""

    async def test_me_success(self, client: AsyncClient, test_user, auth_headers):
        """Test getting current user info."""
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["id"] == test_user.id

    async def test_me_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401
