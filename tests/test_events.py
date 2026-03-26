"""
tests/test_events.py

Integration tests for:
  GET    /events/
  POST   /events/
  PUT    /events/:id/
  DELETE /events/:id/
  POST   /events/:id/register/
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.events.models import Event, Registration
from .factories import UserFactory, EventFactory, RegistrationFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def auth_client(user) -> APIClient:
    """Return an APIClient with a valid Bearer token for user."""
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def future_date(days=7) -> str:
    return (timezone.now() + timedelta(days=days)).isoformat()


def past_date(days=1) -> str:
    return (timezone.now() - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# GET /events/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestListEvents:

    def test_list_events_public(self):
        EventFactory.create_batch(3)
        client = APIClient()   # unauthenticated
        response = client.get(reverse("event-list-create"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 3

    def test_list_returns_registration_count(self):
        event = EventFactory()
        RegistrationFactory.create_batch(2, event=event)
        client = APIClient()
        response = client.get(reverse("event-list-create"))
        assert response.json()[0]["registration_count"] == 2


# ---------------------------------------------------------------------------
# POST /events/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateEvent:

    def test_create_event_authenticated(self):
        user = UserFactory()
        client = auth_client(user)
        payload = {"title": "Tech Talk", "date": future_date(), "location": "Nairobi"}
        response = client.post(reverse("event-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["organizer"]["email"] == user.email

    def test_create_event_unauthenticated(self):
        client = APIClient()
        payload = {"title": "Tech Talk", "date": future_date()}
        response = client.post(reverse("event-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_event_past_date(self):
        user = UserFactory()
        client = auth_client(user)
        payload = {"title": "Old Event", "date": past_date()}
        response = client.post(reverse("event-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_event_missing_title(self):
        user = UserFactory()
        client = auth_client(user)
        payload = {"date": future_date()}
        response = client.post(reverse("event-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# PUT /events/:id/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUpdateEvent:

    def test_organizer_can_update(self):
        user = UserFactory()
        event = EventFactory(organizer=user)
        client = auth_client(user)
        payload = {"title": "Updated Title", "date": future_date(days=10)}
        response = client.put(reverse("event-detail", args=[event.pk]), payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Updated Title"

    def test_non_organizer_cannot_update(self):
        event = EventFactory()
        other_user = UserFactory()
        client = auth_client(other_user)
        payload = {"title": "Hijacked", "date": future_date()}
        response = client.put(reverse("event-detail", args=[event.pk]), payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_nonexistent_event(self):
        user = UserFactory()
        client = auth_client(user)
        response = client.put(reverse("event-detail", args=[9999]), {"title": "x", "date": future_date()}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# DELETE /events/:id/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDeleteEvent:

    def test_organizer_can_delete(self):
        user = UserFactory()
        event = EventFactory(organizer=user)
        client = auth_client(user)
        response = client.delete(reverse("event-detail", args=[event.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert not Event.objects.filter(pk=event.pk).exists()

    def test_non_organizer_cannot_delete(self):
        event = EventFactory()
        other = UserFactory()
        client = auth_client(other)
        response = client.delete(reverse("event-detail", args=[event.pk]))
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# POST /events/:id/register/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestEventRegistration:

    def test_register_success(self):
        user = UserFactory()
        event = EventFactory()
        client = auth_client(user)
        response = client.post(reverse("event-register", args=[event.pk]))
        assert response.status_code == status.HTTP_201_CREATED
        assert Registration.objects.filter(user=user, event=event).exists()

    def test_register_duplicate_blocked(self):
        user = UserFactory()
        event = EventFactory()
        RegistrationFactory(user=user, event=event)
        client = auth_client(user)
        response = client.post(reverse("event-register", args=[event.pk]))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_full_event_blocked(self):
        event = EventFactory(max_attendees=1)
        # Fill the one slot
        RegistrationFactory(event=event)
        user = UserFactory()
        client = auth_client(user)
        response = client.post(reverse("event-register", args=[event.pk]))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_unauthenticated(self):
        event = EventFactory()
        client = APIClient()
        response = client.post(reverse("event-register", args=[event.pk]))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_register_nonexistent_event(self):
        user = UserFactory()
        client = auth_client(user)
        response = client.post(reverse("event-register", args=[9999]))
        assert response.status_code == status.HTTP_404_NOT_FOUND
