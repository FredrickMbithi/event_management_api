"""
apps/events/models.py

Two models:
  Event        — the thing being managed
  Registration — join table between User and Event (with duplicate guard)

Design decisions:
  - organizer FK with PROTECT prevents accidental cascade-deletion of events
    when a user is deactivated — you'd handle orphaned events explicitly
  - Registration uses unique_together to enforce the DB-level duplicate guard
    (the serializer also checks, but DB constraints are the real safety net)
  - max_attendees=None means unlimited; check available_slots in the serializer
"""

from django.db import models
from django.conf import settings


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    date = models.DateTimeField(db_index=True)          # must be in the future on create/update
    max_attendees = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Leave blank for unlimited capacity",
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,                       # block deletion of organizer user
        related_name="organized_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "events"
        ordering = ["date"]
        indexes = [
            models.Index(fields=["date", "organizer"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} @ {self.date:%Y-%m-%d %H:%M}"

    @property
    def registration_count(self) -> int:
        return self.registrations.count()

    @property
    def is_full(self) -> bool:
        if self.max_attendees is None:
            return False
        return self.registration_count >= self.max_attendees


class Registration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registrations"
        # DB-level duplicate prevention — serializer checks first for a cleaner error msg
        unique_together = ("user", "event")
        ordering = ["-registered_at"]
        indexes = [
            models.Index(fields=["user", "event"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.event}"
