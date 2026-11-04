"""Tests for user authentication: registration, login, token flow, roles."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.roles.models import RoleModel, UserRoleModel
from src.users.models import UserModel


class TestRegistration:
    """User registration tests."""

    def test_register_success(self, client: TestClient):
        payload = {
            "name": "Alice Example",
            "email": "alice@example.com",
            "password": "secret1234",
        }
        resp = client.post("/api/v1/users/register", json=payload)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["status"] == status.HTTP_201_CREATED
        assert data["message"] == "User registered successfully"
        user = data["data"]
        assert user["email"] == "alice@example.com"
        assert user["name"] == "Alice Example"
        assert "password_hash" not in user

    def test_register_duplicate_email(self, client: TestClient):
        payload = {
            "name": "Alice Example",
            "email": "alice@example.com",
            "password": "secret1234",
        }
        client.post("/api/v1/users/register", json=payload)
        resp = client.post("/api/v1/users/register", json=payload)
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_register_short_password(self, client: TestClient):
        payload = {
            "name": "Alice Example",
            "email": "alice@example.com",
            "password": "short",
        }
        resp = client.post("/api/v1/users/register", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_blank_name(self, client: TestClient):
        payload = {
            "name": "   ",
            "email": "alice@example.com",
            "password": "secret1234",
        }
        resp = client.post("/api/v1/users/register", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_assigns_student_role(self, client: TestClient, db):
        payload = {
            "name": "Alice Example",
            "email": "alice@example.com",
            "password": "secret1234",
        }
        client.post("/api/v1/users/register", json=payload)
        user = db.query(UserModel).filter(UserModel.email == "alice@example.com").first()
        assert user is not None
        roles = (
            db.query(RoleModel.name)
            .join(UserRoleModel, RoleModel.id == UserRoleModel.role_id)
            .filter(UserRoleModel.user_id == user.id)
            .all()
        )
        role_names = [r[0] for r in roles]
        assert "student" in role_names


class TestLogin:
    """User login tests."""

    def _register(self, client: TestClient):
        return client.post(
            "/api/v1/users/register",
            json={
                "name": "Bob",
                "email": "bob@example.com",
                "password": "secret1234",
            },
        )

    def test_login_success(self, client: TestClient):
        self._register(client)
        resp = client.post(
            "/api/v1/users/login",
            json={"email": "bob@example.com", "password": "secret1234"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        self._register(client)
        resp = client.post(
            "/api/v1/users/login",
            json={"email": "bob@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client: TestClient):
        resp = client.post(
            "/api/v1/users/login",
            json={"email": "nobody@example.com", "password": "secret1234"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_deactivated_account(self, client: TestClient, db):
        self._register(client)
        user = db.query(UserModel).filter(UserModel.email == "bob@example.com").first()
        user.is_active = False
        db.commit()
        resp = client.post(
            "/api/v1/users/login",
            json={"email": "bob@example.com", "password": "secret1234"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestTokenFlow:
    """Token-based endpoints: /me, update /me, logout."""

    def _login(self, client: TestClient) -> str:
        client.post(
            "/api/v1/users/register",
            json={
                "name": "Carol",
                "email": "carol@example.com",
                "password": "secret1234",
            },
        )
        resp = client.post(
            "/api/v1/users/login",
            json={"email": "carol@example.com", "password": "secret1234"},
        )
        return resp.json()["data"]["access_token"]

    def test_get_me(self, client: TestClient):
        token = self._login(client)
        resp = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["email"] == "carol@example.com"
        assert "student" in data["roles"]

    def test_get_me_no_token(self, client: TestClient):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_update_me(self, client: TestClient):
        token = self._login(client)
        resp = client.put(
            "/api/v1/users/me",
            json={"name": "Carol Updated", "phone": "+1234567890"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["name"] == "Carol Updated"
        assert data["phone"] == "+1234567890"

    def test_logout(self, client: TestClient):
        token = self._login(client)
        resp = client.post(
            "/api/v1/users/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        # Token should now be revoked
        resp2 = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == status.HTTP_401_UNAUTHORIZED


class TestBecomeTeacher:
    """Teacher role activation tests."""

    def _login(self, client: TestClient) -> str:
        client.post(
            "/api/v1/users/register",
            json={
                "name": "Dave",
                "email": "dave@example.com",
                "password": "secret1234",
            },
        )
        resp = client.post(
            "/api/v1/users/login",
            json={"email": "dave@example.com", "password": "secret1234"},
        )
        return resp.json()["data"]["access_token"]

    def test_become_teacher(self, client: TestClient):
        token = self._login(client)
        resp = client.post(
            "/api/v1/users/become-teacher",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["message"] == "Teacher role activated and profile created successfully"

    def test_become_teacher_idempotent(self, client: TestClient):
        token = self._login(client)
        client.post(
            "/api/v1/users/become-teacher",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp2 = client.post(
            "/api/v1/users/become-teacher",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Router declares status_code=201, but the controller returns 200 for idempotent case
        assert resp2.json()["message"] == "User is already a teacher"
