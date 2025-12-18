"""Tests for task endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCreateTask:
    """Tests for POST /api/projects/{project_id}/tasks"""

    async def test_create_task_success(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test successful task creation."""
        response = await client.post(
            f"/api/projects/{test_project.id}/tasks",
            json={
                "title": "New Task",
                "description": "Task description",
                "status": "todo",
                "complexity": "medium",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert data["status"] == "todo"
        assert data["complexity"] == "medium"
        assert data["project_id"] == test_project.id
        assert data["creator"]["username"] == "testuser"

    async def test_create_task_minimal(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating task with minimal data."""
        response = await client.post(
            f"/api/projects/{test_project.id}/tasks",
            json={"title": "Minimal Task"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["status"] == "todo"  # Default
        assert data["complexity"] == "medium"  # Default

    async def test_create_task_with_assignee(
        self, client: AsyncClient, auth_headers, test_project, test_user
    ):
        """Test creating task with assignee."""
        response = await client.post(
            f"/api/projects/{test_project.id}/tasks",
            json={"title": "Assigned Task", "assignee_id": test_user.id},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["assignee"]["id"] == test_user.id

    async def test_create_task_with_member_assignee(
        self, client: AsyncClient, auth_headers, test_project_with_member, test_user2
    ):
        """Test creating task with member as assignee."""
        response = await client.post(
            f"/api/projects/{test_project_with_member.id}/tasks",
            json={"title": "Member Task", "assignee_id": test_user2.id},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["assignee"]["id"] == test_user2.id

    async def test_create_task_invalid_assignee(
        self, client: AsyncClient, auth_headers, test_project, test_user2
    ):
        """Test creating task with non-member assignee."""
        response = await client.post(
            f"/api/projects/{test_project.id}/tasks",
            json={"title": "Invalid Task", "assignee_id": test_user2.id},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Assignee must be project owner or member" in response.json()["detail"]

    async def test_create_task_project_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating task in non-existent project."""
        response = await client.post(
            "/api/projects/99999/tasks",
            json={"title": "Task"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_create_task_no_access(
        self, client: AsyncClient, auth_headers_user2, test_project
    ):
        """Test creating task without project access."""
        response = await client.post(
            f"/api/projects/{test_project.id}/tasks",
            json={"title": "Unauthorized Task"},
            headers=auth_headers_user2,
        )
        assert response.status_code == 403

    async def test_create_task_as_member(
        self, client: AsyncClient, auth_headers_user2, test_project_with_member
    ):
        """Test creating task as project member."""
        response = await client.post(
            f"/api/projects/{test_project_with_member.id}/tasks",
            json={"title": "Member Created Task"},
            headers=auth_headers_user2,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["creator"]["username"] == "testuser2"


class TestGetTasks:
    """Tests for GET /api/projects/{project_id}/tasks"""

    async def test_get_tasks_empty(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test getting tasks when project has none."""
        response = await client.get(
            f"/api/projects/{test_project.id}/tasks", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_tasks_success(
        self, client: AsyncClient, auth_headers, test_project, test_task
    ):
        """Test getting tasks."""
        response = await client.get(
            f"/api/projects/{test_project.id}/tasks", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Task"

    async def test_get_tasks_no_access(
        self, client: AsyncClient, auth_headers_user2, test_project
    ):
        """Test getting tasks without access."""
        response = await client.get(
            f"/api/projects/{test_project.id}/tasks", headers=auth_headers_user2
        )
        assert response.status_code == 403


class TestGetTask:
    """Tests for GET /api/projects/{project_id}/tasks/{task_id}"""

    async def test_get_task_success(
        self, client: AsyncClient, auth_headers, test_project, test_task
    ):
        """Test getting single task."""
        response = await client.get(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["id"] == test_task.id

    async def test_get_task_not_found(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test getting non-existent task."""
        response = await client.get(
            f"/api/projects/{test_project.id}/tasks/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateTask:
    """Tests for PUT /api/projects/{project_id}/tasks/{task_id}"""

    async def test_update_task_success(
        self, client: AsyncClient, auth_headers, test_project, test_task
    ):
        """Test updating task."""
        response = await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={
                "title": "Updated Task",
                "description": "Updated description",
                "status": "in_progress",
                "complexity": "high",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task"
        assert data["description"] == "Updated description"
        assert data["status"] == "in_progress"
        assert data["complexity"] == "high"

    async def test_update_task_partial(
        self, client: AsyncClient, auth_headers, test_project, test_task
    ):
        """Test partial task update."""
        response = await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={"status": "done"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["title"] == "Test Task"  # Unchanged

    async def test_update_task_set_assignee(
        self, client: AsyncClient, auth_headers, test_project, test_task, test_user
    ):
        """Test setting task assignee."""
        response = await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={"assignee_id": test_user.id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assignee"]["id"] == test_user.id

    async def test_update_task_clear_assignee(
        self, client: AsyncClient, auth_headers, test_project, test_task, test_user
    ):
        """Test clearing task assignee."""
        # First set assignee
        await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={"assignee_id": test_user.id},
            headers=auth_headers,
        )

        # Then clear it
        response = await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={"assignee_id": None},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assignee"] is None

    async def test_update_task_invalid_assignee(
        self, client: AsyncClient, auth_headers, test_project, test_task, test_user2
    ):
        """Test setting non-member as assignee."""
        response = await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={"assignee_id": test_user2.id},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_update_task_no_access(
        self, client: AsyncClient, auth_headers_user2, test_project, test_task
    ):
        """Test updating task without access."""
        response = await client.put(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            json={"title": "Hacked"},
            headers=auth_headers_user2,
        )
        assert response.status_code == 403

    async def test_update_task_as_member(
        self,
        client: AsyncClient,
        auth_headers_user2,
        test_project_with_member,
        db_session,
        test_user,
    ):
        """Test updating task as member."""
        from app.models import Task, TaskStatus, TaskComplexity

        # Create task in project
        task = Task(
            title="Task to update",
            status=TaskStatus.TODO,
            complexity=TaskComplexity.LOW,
            project_id=test_project_with_member.id,
            creator_id=test_user.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.put(
            f"/api/projects/{test_project_with_member.id}/tasks/{task.id}",
            json={"status": "done"},
            headers=auth_headers_user2,
        )
        assert response.status_code == 200


class TestDeleteTask:
    """Tests for DELETE /api/projects/{project_id}/tasks/{task_id}"""

    async def test_delete_task_success(
        self, client: AsyncClient, auth_headers, test_project, test_task
    ):
        """Test deleting task."""
        response = await client.delete(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify task is deleted
        response = await client.get(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_task_not_found(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test deleting non-existent task."""
        response = await client.delete(
            f"/api/projects/{test_project.id}/tasks/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_task_no_access(
        self, client: AsyncClient, auth_headers_user2, test_project, test_task
    ):
        """Test deleting task without access."""
        response = await client.delete(
            f"/api/projects/{test_project.id}/tasks/{test_task.id}",
            headers=auth_headers_user2,
        )
        assert response.status_code == 403
