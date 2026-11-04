"""Tests for learning request lifecycle."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.category.models import CategoryModel


class TestLearningRequests:
    """Learning request lifecycle tests."""

    def _teacher_token(self, client: TestClient, email: str) -> str:
        client.post(
            "/api/v1/users/register",
            json={"name": "Req Teacher", "email": email, "password": "secret1234"},
        )
        resp = client.post(
            "/api/v1/users/login",
            json={"email": email, "password": "secret1234"},
        )
        token = resp.json()["data"]["access_token"]
        client.post(
            "/api/v1/users/become-teacher",
            headers={"Authorization": f"Bearer {token}"},
        )
        return token

    def _student_token(self, client: TestClient, email: str) -> str:
        client.post(
            "/api/v1/users/register",
            json={"name": "Req Student", "email": email, "password": "secret1234"},
        )
        resp = client.post(
            "/api/v1/users/login",
            json={"email": email, "password": "secret1234"},
        )
        return resp.json()["data"]["access_token"]

    def _get_category_id(self, db) -> int:
        cat = db.query(CategoryModel).first()
        if cat is None:
            cat = CategoryModel(name="Technology", slug="technology")
            db.add(cat)
            db.commit()
            db.refresh(cat)
        return cat.id

    def _create_published_skill(self, client: TestClient, db, token: str) -> int:
        category_id = self._get_category_id(db)
        resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Math Tutoring",
                "description": "Learn math",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        skill_id = resp.json()["data"]["id"]
        client.patch(
            f"/api/v1/skills/{skill_id}/status",
            json={"status": "published"},
            headers={"Authorization": f"Bearer {token}"},
        )
        return skill_id

    def test_create_learning_request(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t1@example.com")
        student_token = self._student_token(client, "lr_s1@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "I want to learn math"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()["data"]
        assert data["status"] == "pending"

    def test_self_request_prevented(self, client: TestClient, db):
        """A teacher cannot send a request to their own skill."""
        teacher_token = self._teacher_token(client, "lr_self@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Self request"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_teacher_accepts_request(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t2@example.com")
        student_token = self._student_token(client, "lr_s2@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        create_resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Please teach me"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        request_id = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["status"] == "accepted"

    def test_teacher_rejects_request(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t3@example.com")
        student_token = self._student_token(client, "lr_s3@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        create_resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Please teach me"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        request_id = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/requests/{request_id}/reject",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["status"] == "rejected"

    def test_student_cancels_request(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t4@example.com")
        student_token = self._student_token(client, "lr_s4@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        create_resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Please teach me"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        request_id = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/requests/{request_id}/cancel",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["status"] == "cancelled"

    def test_list_sent_requests(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t5@example.com")
        student_token = self._student_token(client, "lr_s5@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Hello"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        resp = client.get(
            "/api/v1/requests/sent",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) >= 1

    def test_list_received_requests(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t6@example.com")
        student_token = self._student_token(client, "lr_s6@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Hello"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        resp = client.get(
            "/api/v1/requests/received",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) >= 1

    def test_non_participant_cannot_view_request(self, client: TestClient, db):
        teacher_token = self._teacher_token(client, "lr_t7@example.com")
        student_token = self._student_token(client, "lr_s7@example.com")
        other_token = self._student_token(client, "lr_other@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        create_resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Hello"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        request_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/requests/{request_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_accept_non_pending_request(self, client: TestClient, db):
        """Accepting an already-accepted request should fail."""
        teacher_token = self._teacher_token(client, "lr_t8@example.com")
        student_token = self._student_token(client, "lr_s8@example.com")
        skill_id = self._create_published_skill(client, db, teacher_token)

        create_resp = client.post(
            "/api/v1/requests",
            json={"skill_listing_id": skill_id, "message": "Hello"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        request_id = create_resp.json()["data"]["id"]

        # Accept once
        client.patch(
            f"/api/v1/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        # Try to accept again
        resp = client.patch(
            f"/api/v1/requests/{request_id}/accept",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
