"""apps/events/urls.py"""

from django.urls import path
from .views import EventListCreateView, EventDetailView, EventRegisterView

urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list-create"),
    path("<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("<int:pk>/register/", EventRegisterView.as_view(), name="event-register"),
]
