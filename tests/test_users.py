"""
tests/test_users.py

Unit + integration tests for:
  POST /users/register
  POST /users/login

Covers: happy paths, validation failures, duplicate email, wrong credentials.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from .factories import UserFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def register_url():
    return reverse("user-register")


@pytest.fixture
def login_url():
    return reverse("user-login")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserRegistration:

    def test_register_success(self, client, register_url):
        payload = {"name": "Ghost", "email": "ghost@example.com", "password": "secure123"}
        response = client.post(register_url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user"]["email"] == "ghost@example.com"
        assert "tokens" in data
        assert "access" in data["tokens"]
        assert "password" not in data["user"]   # never leak the hash

    def test_register_hashes_password(self, client, register_url):
        payload = {"name": "Ghost", "email": "ghost@example.com", "password": "secure123"}
        client.post(register_url, payload, format="json")
        user = User.objects.get(email="ghost@example.com")
        # check_password uses the hashing algorithm — raw string must NOT match stored value
        assert user.password != "secure123"
        assert user.check_password("secure123")

    def test_register_duplicate_email(self, client, register_url):
        UserFactory(email="taken@example.com")
        payload = {"name": "Other", "email": "taken@example.com", "password": "secure123"}
        response = client.post(register_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email(self, client, register_url):
        payload = {"name": "Ghost", "email": "not-an-email", "password": "secure123"}
        response = client.post(register_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, client, register_url):
        payload = {"name": "Ghost", "email": "ghost@example.com", "password": "abc"}
        response = client.post(register_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    def test_register_missing_fields(self, client, register_url):
        response = client.post(register_url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserLogin:

    def test_login_success(self, client, login_url):
        user = UserFactory(email="ghost@example.com")
        user.set_password("testpass123")
        user.save()

        response = client.post(login_url, {"email": "ghost@example.com", "password": "testpass123"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tokens" in data
        assert data["user"]["email"] == "ghost@example.com"

    def test_login_wrong_password(self, client, login_url):
        UserFactory(email="ghost@example.com")
        response = client.post(login_url, {"email": "ghost@example.com", "password": "wrongpass"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_email(self, client, login_url):
        response = client.post(login_url, {"email": "nobody@example.com", "password": "pass123"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, client, login_url):
        user = UserFactory(email="ghost@example.com", is_active=False)
        user.set_password("testpass123")
        user.save()
        response = client.post(login_url, {"email": "ghost@example.com", "password": "testpass123"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
