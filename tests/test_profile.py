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
