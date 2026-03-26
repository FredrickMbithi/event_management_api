"""
apps/users/serializers.py

Serializers handle two jobs here:
1. Input validation  — reject bad data before it touches the DB
2. Output shaping    — control exactly what fields go back to the client
"""

import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new user.

    Rules:
      - email: standard format check
      - password: minimum 6 characters (write-only — never echoed back)
      - name: non-empty
    """

    password = serializers.CharField(
        write_only=True,        # never included in serialized output
        min_length=6,
        error_messages={"min_length": "Password must be at least 6 characters."},
    )

    class Meta:
        model = User
        fields = ("id", "name", "email", "password", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_email(self, value: str) -> str:
        """Extra email format guard on top of EmailField."""
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def create(self, validated_data: dict) -> User:
        """Delegate to manager so password is always hashed."""
        return User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )


class UserLoginSerializer(serializers.Serializer):
    """
    Validates login credentials.
    Returns the authenticated User instance via .validated_data["user"].
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict) -> dict:
        email = data["email"].lower().strip()
        password = data["password"]

        user = authenticate(
            request=self.context.get("request"),
            username=email,       # AbstractBaseUser uses USERNAME_FIELD
            password=password,
        )

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        data["user"] = user
        return data


class UserPublicSerializer(serializers.ModelSerializer):
    """Read-only serializer — safe to include in event/registration responses."""

    class Meta:
        model = User
        fields = ("id", "name", "email")
