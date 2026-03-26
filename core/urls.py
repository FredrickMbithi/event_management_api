"""core/urls.py — root URL configuration."""

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Users: registration + login
    path("users/", include("apps.users.urls")),

    # Events + registrations
    path("events/", include("apps.events.urls")),

    # JWT token refresh (bonus endpoint — good practice)
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
