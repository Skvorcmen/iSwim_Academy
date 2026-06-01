from django.contrib.auth.models import AbstractUser

from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        FAN = "fan"
        ATHLETE = "athlete"
        COACH = "coach"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FAN,
    )
