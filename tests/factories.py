"""
tests/factories.py

Factory Boy factories — generate realistic test objects without manual setup.
Much cleaner than manually calling Model.objects.create() in every test.
"""

import factory
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User
from apps.events.models import Event, Registration


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    name = factory.Faker("name")
    email = factory.Faker("email")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    location = factory.Faker("city")
    # Always in the future — avoids validation errors in tests
    date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    max_attendees = None   # unlimited by default
    organizer = factory.SubFactory(UserFactory)


class RegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Registration

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
