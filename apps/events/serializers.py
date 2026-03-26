"""
apps/events/serializers.py

EventSerializer      — full CRUD serializer with future-date validation
RegistrationSerializer — handles register + duplicate/capacity checks
"""

from django.utils import timezone
from rest_framework import serializers

from apps.users.serializers import UserPublicSerializer
from .models import Event, Registration


class EventSerializer(serializers.ModelSerializer):
    """
    Used for listing, creating, and updating events.

    Read path:  includes organizer detail + live registration_count
    Write path: organizer is injected from request.user in the view (not client-supplied)
    """

    # Read-only computed/nested fields
    organizer = UserPublicSerializer(read_only=True)
    registration_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "location",
            "date",
            "max_attendees",
            "organizer",
            "registration_count",
            "is_full",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "organizer", "registration_count", "is_full", "created_at", "updated_at")

    def validate_date(self, value):
        """Event date must be in the future."""
        if value <= timezone.now():
            raise serializers.ValidationError("Event date must be in the future.")
        return value

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_max_attendees(self, value):
        """If provided, must be at least 1."""
        if value is not None and value < 1:
            raise serializers.ValidationError("max_attendees must be at least 1.")
        return value

    def create(self, validated_data: dict) -> Event:
        # organizer is passed from the view via serializer.save(organizer=request.user)
        return Event.objects.create(**validated_data)

    def update(self, instance: Event, validated_data: dict) -> Event:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RegistrationSerializer(serializers.ModelSerializer):
    """
    POST /events/:id/register

    Checks:
      1. Not already registered (duplicate)
      2. Event is not full (capacity)
    """

    user = UserPublicSerializer(read_only=True)
    event_id = serializers.IntegerField(read_only=True, source="event.id")
    event_title = serializers.CharField(read_only=True, source="event.title")

    class Meta:
        model = Registration
        fields = ("id", "user", "event_id", "event_title", "registered_at")
        read_only_fields = ("id", "user", "event_id", "event_title", "registered_at")

    def validate(self, data: dict) -> dict:
        user = self.context["request"].user
        event = self.context["event"]

        # Duplicate check (serializer-level gives a clean 400 before hitting the DB constraint)
        if Registration.objects.filter(user=user, event=event).exists():
            raise serializers.ValidationError("You are already registered for this event.")

        # Capacity check
        if event.is_full:
            raise serializers.ValidationError(
                f"This event is fully booked ({event.max_attendees} attendees)."
            )

        return data

    def create(self, validated_data: dict) -> Registration:
        return Registration.objects.create(
            user=self.context["request"].user,
            event=self.context["event"],
        )
