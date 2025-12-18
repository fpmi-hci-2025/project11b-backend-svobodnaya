"""Tests for healthcheck and root endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestHealthcheck:
    """Tests for GET /healthcheck"""

    async def test_healthcheck_success(self, client: AsyncClient):
        """Test healthcheck returns healthy status."""
        response = await client.get("/healthcheck")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "taskflow-api"

    async def test_healthcheck_content_type(self, client: AsyncClient):
        """Test healthcheck returns JSON content type."""
        response = await client.get("/healthcheck")
        assert "application/json" in response.headers["content-type"]


class TestRoot:
    """Tests for GET /"""

    async def test_root_success(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "TaskFlow API"
        assert data["docs"] == "/docs"
