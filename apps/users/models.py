"""
apps/users/models.py

Custom User model — always extend AbstractBaseUser or AbstractUser in Django
rather than using the built-in User, so you control the auth fields cleanly.

We use AbstractBaseUser here for maximum control:
  - email as the login identifier (not username)
  - name as a single full-name field
  - Django's built-in PBKDF2 password hashing (bcrypt-equivalent strength)
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager: email-first creation, no username."""

    def create_user(self, email: str, name: str, password: str, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)   # hashes via PBKDF2+SHA256
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, name: str, password: str, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Application user.

    Fields:
        email       — unique login identifier
        name        — display name
        is_active   — soft-delete / account suspension flag
        is_staff    — admin site access
        created_at  — immutable timestamp
    """

    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # Tell Django to use email as the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"
