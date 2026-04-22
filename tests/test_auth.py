# tests/test_auth.py
"""
Auth tests — registration, login, and token validation.
Uses in-memory SQLite via conftest fixtures.
"""
import pytest
from datetime import timedelta
from jose import jwt
from app.services.auth import get_password_hash, verify_password, create_access_token
from app.config import config


class TestPasswordHashing:
    """Unit tests for password hashing utilities."""

    def test_hash_differs_from_plaintext(self):
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_verify_correct_password(self):
        password = "secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_unique_per_call(self):
        """Argon2 should produce different hashes for the same password (salted)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestAccessToken:
    """Unit tests for JWT token creation."""

    def test_token_contains_subject(self):
        token = create_access_token({"sub": "testuser"})
        decoded = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        assert decoded["sub"] == "testuser"

    def test_token_has_expiry(self):
        token = create_access_token({"sub": "testuser"})
        decoded = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in decoded

    def test_custom_expiry(self):
        token = create_access_token(
            {"sub": "testuser"},
            expires_delta=timedelta(minutes=60),
        )
        decoded = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in decoded


class TestAuthEndpoints:
    """Integration tests for auth API endpoints."""

    def test_register_success(self, client):
        response = client.post("/auth/register", json={
            "username": "newuser",
            "password": "password123",
            "role": "user",
            "date_of_birth": "1995-06-15",
            "phone": "+84987654321",
            "email": "new@example.com",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"

    def test_register_duplicate_username(self, client, test_user):
        response = client.post("/auth/register", json={
            "username": "testuser",  # Already exists via test_user fixture
            "password": "password123",
            "role": "user",
            "date_of_birth": "1995-06-15",
            "phone": "+84111222333",
            "email": "dup@example.com",
        })
        assert response.status_code == 409

    def test_login_success(self, client, test_user):
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "wrong_password",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", data={
            "username": "ghost_user",
            "password": "password123",
        })
        assert response.status_code == 401
