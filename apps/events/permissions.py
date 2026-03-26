"""
apps/events/permissions.py

IsOrganizerOrReadOnly:
  - Safe methods (GET, HEAD, OPTIONS) — always allowed
  - Unsafe methods (PUT, PATCH, DELETE) — only the event's organizer
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOrganizerOrReadOnly(BasePermission):
    """
    Object-level permission: write access only for the event organizer.

    Usage:
        self.check_object_permissions(request, event_instance)
    """

    message = "Only the event organizer can modify or delete this event."

    def has_permission(self, request, view) -> bool:
        # View-level: authenticated users pass; AllowAny handled in view's get_permissions
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj) -> bool:
        # Read operations are always safe
        if request.method in SAFE_METHODS:
            return True
        # Write operations: must be the organizer
        return obj.organizer == request.user
