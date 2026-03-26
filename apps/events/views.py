"""
apps/events/views.py

EventListCreateView     GET /events/         — public list
                        POST /events/        — auth required
EventDetailView         PUT /events/:id/     — auth required
                        DELETE /events/:id/  — auth required
EventRegisterView       POST /events/:id/register — auth required

Permission strategy:
  - Listing events is public (AllowAny)
  - Creating/updating/deleting requires authentication
  - Only the event organizer can update or delete their own event
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Event, Registration
from .serializers import EventSerializer, RegistrationSerializer
from .permissions import IsOrganizerOrReadOnly


class EventListCreateView(APIView):
    """
    GET  /events/  — list all upcoming events (public)
    POST /events/  — create a new event (auth required)
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        events = Event.objects.select_related("organizer").prefetch_related("registrations")
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(organizer=request.user)   # inject authenticated user
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    """
    PUT    /events/:id/  — update (organizer only)
    DELETE /events/:id/  — delete (organizer only)
    """

    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]

    def _get_event(self, pk: int) -> Event:
        try:
            return Event.objects.select_related("organizer").get(pk=pk)
        except Event.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Event with id={pk} not found.")

    def put(self, request, pk: int):
        event = self._get_event(pk)
        self.check_object_permissions(request, event)   # triggers IsOrganizerOrReadOnly

        serializer = EventSerializer(event, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk: int):
        """Bonus: partial update — not in spec but trivial to add."""
        event = self._get_event(pk)
        self.check_object_permissions(request, event)

        serializer = EventSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        event = self._get_event(pk)
        self.check_object_permissions(request, event)
        event.delete()
        return Response(
            {"message": f"Event '{event.title}' deleted."},
            status=status.HTTP_200_OK,
        )


class EventRegisterView(APIView):
    """
    POST /events/:id/register — register authenticated user for an event.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Event with id={pk} not found.")

        serializer = RegistrationSerializer(
            data={},
            context={"request": request, "event": event},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": f"Successfully registered for '{event.title}'.",
                "registration": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
