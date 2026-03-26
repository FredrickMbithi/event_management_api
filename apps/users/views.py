"""
apps/users/views.py

Two public endpoints (no auth required):
  POST /users/register  — create account
  POST /users/login     — authenticate, get JWT pair
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegistrationSerializer, UserLoginSerializer


def _token_pair(user) -> dict:
    """Generate access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class RegisterView(APIView):
    """
    POST /users/register

    Body: { "name": str, "email": str, "password": str }
    Returns: user object + JWT tokens (201)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)   # 400 on failure via exception handler
        user = serializer.save()

        return Response(
            {
                "user": serializer.data,
                "tokens": _token_pair(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /users/login

    Body: { "email": str, "password": str }
    Returns: JWT access + refresh tokens (200)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return Response(
            {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                },
                "tokens": _token_pair(user),
            },
            status=status.HTTP_200_OK,
        )
