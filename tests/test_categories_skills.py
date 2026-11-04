"""Tests for categories and skill listings."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.category.models import CategoryModel


class TestCategories:
    """Category API tests."""

    def test_list_categories(self, client: TestClient):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == status.HTTP_200_OK
        assert isinstance(data["data"], list)

    def test_get_category_by_id(self, client: TestClient, db):
        # Seed a category
        cat = CategoryModel(name="Test Cat", slug="test-cat")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        resp = client.get(f"/api/v1/categories/{cat.id}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["name"] == "Test Cat"

    def test_get_category_not_found(self, client: TestClient):
        resp = client.get("/api/v1/categories/9999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestSkillListings:
    """Skill listing CRUD tests."""

    def _teacher_token(self, client: TestClient, email: str) -> str:
        """Register, login, and become a teacher — return token."""
        client.post(
            "/api/v1/users/register",
            json={"name": "Skill Teacher", "email": email, "password": "secret1234"},
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
            json={"name": "Student One", "email": email, "password": "secret1234"},
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

    def test_create_skill_listing(self, client: TestClient, db):
        token = self._teacher_token(client, "skill1@example.com")
        category_id = self._get_category_id(db)
        resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Learn Python",
                "description": "Python for beginners",
                "category_id": category_id,
                "level": "beginner",
                "price_amount": 500,
                "teaching_mode": "online",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()["data"]
        assert data["title"] == "Learn Python"

    def test_create_skill_as_student_fails(self, client: TestClient, db):
        token = self._student_token(client, "skill_student@example.com")
        category_id = self._get_category_id(db)
        resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Hack",
                "description": "Should fail",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_published_skills(self, client: TestClient, db):
        token = self._teacher_token(client, "skill2@example.com")
        category_id = self._get_category_id(db)
        # Create and publish
        create_resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Published Skill",
                "description": "Visible to all",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        skill_id = create_resp.json()["data"]["id"]
        client.patch(
            f"/api/v1/skills/{skill_id}/status",
            json={"status": "published"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get("/api/v1/skills")
        assert resp.status_code == status.HTTP_200_OK
        items = resp.json()["data"]
        titles = [s["title"] for s in items]
        assert "Published Skill" in titles

    def test_update_own_skill(self, client: TestClient, db):
        token = self._teacher_token(client, "skill3@example.com")
        category_id = self._get_category_id(db)
        create_resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Original Title",
                "description": "Desc",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        skill_id = create_resp.json()["data"]["id"]
        resp = client.put(
            f"/api/v1/skills/{skill_id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["title"] == "Updated Title"

    def test_update_other_skill_fails(self, client: TestClient, db):
        token_a = self._teacher_token(client, "skill4a@example.com")
        token_b = self._teacher_token(client, "skill4b@example.com")
        category_id = self._get_category_id(db)
        create_resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Teacher A Skill",
                "description": "Desc",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        skill_id = create_resp.json()["data"]["id"]
        resp = client.put(
            f"/api/v1/skills/{skill_id}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_archive_skill(self, client: TestClient, db):
        token = self._teacher_token(client, "skill5@example.com")
        category_id = self._get_category_id(db)
        create_resp = client.post(
            "/api/v1/skills",
            json={
                "title": "To Archive",
                "description": "Desc",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        skill_id = create_resp.json()["data"]["id"]
        resp = client.delete(
            f"/api/v1/skills/{skill_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_search_skills(self, client: TestClient, db):
        token = self._teacher_token(client, "skill6@example.com")
        category_id = self._get_category_id(db)
        create_resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Guitar Lessons",
                "description": "Learn guitar fast",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        skill_id = create_resp.json()["data"]["id"]
        client.patch(
            f"/api/v1/skills/{skill_id}/status",
            json={"status": "published"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get("/api/v1/skills/search", params={"query": "guitar"})
        assert resp.status_code == status.HTTP_200_OK
        items = resp.json()["data"]
        assert any("Guitar" in s["title"] for s in items)

    def test_negative_price_rejected(self, client: TestClient, db):
        token = self._teacher_token(client, "skill7@example.com")
        category_id = self._get_category_id(db)
        resp = client.post(
            "/api/v1/skills",
            json={
                "title": "Bad Price",
                "description": "Desc",
                "category_id": category_id,
                "price_amount": -10,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
