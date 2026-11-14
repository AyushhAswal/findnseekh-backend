"""Tests for teacher profile CRUD operations."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTeacherProfile:
    """Teacher profile tests."""

    def _register_and_login(self, client: TestClient, email: str) -> str:
        client.post(
            "/api/v1/users/register",
            json={"name": "Teacher One", "email": email, "password": "secret1234"},
        )
        resp = client.post(
            "/api/v1/users/login",
            json={"email": email, "password": "secret1234"},
        )
        return resp.json()["data"]["access_token"]

    def _become_teacher(self, client: TestClient, token: str):
        client.post(
            "/api/v1/users/become-teacher",
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_get_my_profile(self, client: TestClient):
        token = self._register_and_login(client, "tp1@example.com")
        self._become_teacher(client, token)
        resp = client.get(
            "/api/v1/profile/teacher/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["teaching_mode"] == "both"
        assert data["experience_years"] == 0

    def test_update_my_profile(self, client: TestClient):
        token = self._register_and_login(client, "tp2@example.com")
        self._become_teacher(client, token)
        resp = client.put(
            "/api/v1/profile/teacher/me",
            json={
                "bio": "Experienced Python tutor",
                "qualification": "M.Sc. Computer Science",
                "skills": ["Python", "Machine Learning", "Mathematics"],
                "experience_years": 5,
                "city": "Bangalore",
                "teaching_mode": "online",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["bio"] == "Experienced Python tutor"
        assert data["qualification"] == "M.Sc. Computer Science"
        assert data["skills"] == ["Python", "Machine Learning", "Mathematics"]
        assert data["experience_years"] == 5
        assert data["city"] == "Bangalore"
        assert data["teaching_mode"] == "online"

    def test_get_public_profile(self, client: TestClient):
        token = self._register_and_login(client, "tp3@example.com")
        self._become_teacher(client, token)
        client.put(
            "/api/v1/profile/teacher/me",
            json={
                "skills": ["Guitar", "Music Theory"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # Get user_id from /me
        me_resp = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        user_id = me_resp.json()["data"]["id"]
        resp = client.get(f"/api/v1/profile/teacher/{user_id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["name"] == "Teacher One"
        assert data["skills"] == ["Guitar", "Music Theory"]
        assert "password_hash" not in data

    def test_get_public_profile_not_found(self, client: TestClient):
        resp = client.get("/api/v1/profile/teacher/9999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_teaching_mode(self, client: TestClient):
        token = self._register_and_login(client, "tp4@example.com")
        self._become_teacher(client, token)
        resp = client.put(
            "/api/v1/profile/teacher/me",
            json={"teaching_mode": "invalid_mode"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestStudentProfile:
    """Student profile tests."""

    def _register_and_login(self, client: TestClient, email: str) -> str:
        client.post(
            "/api/v1/users/register",
            json={"name": "Student One", "email": email, "password": "secret1234"},
        )
        resp = client.post(
            "/api/v1/users/login",
            json={"email": email, "password": "secret1234"},
        )
        return resp.json()["data"]["access_token"]

    def test_get_my_student_profile(self, client: TestClient):
        token = self._register_and_login(client, "student1@example.com")
        resp = client.get(
            "/api/v1/profile/student/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["learning_mode"] == "both"
        assert data["learning_level"] == "beginner"
        assert data["skills_to_learn"] == []

    def test_update_my_student_profile(self, client: TestClient):
        token = self._register_and_login(client, "student2@example.com")
        resp = client.put(
            "/api/v1/profile/student/me",
            json={
                "phone": "+91 9876543210",
                "city": "Bengaluru",
                "state": "Karnataka",
                "learning_mode": "online",
                "learning_level": "intermediate",
                "learning_goals": "Want to learn acoustic guitar fingerstyle",
                "skills_to_learn": ["Guitar", "Music Theory"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["phone"] == "+91 9876543210"
        assert data["city"] == "Bengaluru"
        assert data["state"] == "Karnataka"
        assert data["learning_mode"] == "online"
        assert data["learning_level"] == "intermediate"
        assert data["learning_goals"] == "Want to learn acoustic guitar fingerstyle"
        assert data["skills_to_learn"] == ["Guitar", "Music Theory"]

    def test_invalid_learning_mode(self, client: TestClient):
        token = self._register_and_login(client, "student3@example.com")
        resp = client.put(
            "/api/v1/profile/student/me",
            json={"learning_mode": "invalid"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, 422)

    def test_invalid_learning_level(self, client: TestClient):
        token = self._register_and_login(client, "student4@example.com")
        resp = client.put(
            "/api/v1/profile/student/me",
            json={"learning_level": "grandmaster"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, 422)
