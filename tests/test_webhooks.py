"""Tests for Meta WhatsApp webhook endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    # Import here to avoid import errors if dependencies aren't installed
    from checkup.main import app
    return TestClient(app)


class TestWebhookVerification:
    """Tests for GET /api/webhook (Meta verification)."""

    def test_valid_verification(self, client):
        """Should return challenge on valid verify token."""
        from checkup.config import settings
        response = client.get("/api/webhook", params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.meta_verify_token,
            "hub.challenge": "test_challenge_123",
        })
        assert response.status_code == 200
        assert response.text == "test_challenge_123"

    def test_invalid_token(self, client):
        """Should reject invalid verify token."""
        response = client.get("/api/webhook", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "test_challenge_123",
        })
        assert response.status_code == 403


class TestHealthCheck:
    """Tests for GET /health."""

    def test_health_check(self, client):
        """Should return ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
