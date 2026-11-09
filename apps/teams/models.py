from django.db import models
from apps.core.models import TimeStampedModel
from apps.users.models import User


class Team(TimeStampedModel):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    coach = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="teams"
    )

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"

    def __str__(self):
        return f"{self.name} — {self.city}"


class Athlete(TimeStampedModel):

    class Gender(models.TextChoices):
        MALE = "male", "Мужской"
        FEMALE = "female", "Женский"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_year = models.IntegerField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="athletes")
    coach = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="athletes"
    )
    application = models.ForeignKey(
        "competitions.Application",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="athletes",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="athlete_profiles",
        verbose_name="Профиль на портале",
    )

    class Meta:
        verbose_name = "Спортсмен"
        verbose_name_plural = "Спортсмены"

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.birth_year}"


from django.db.models import Q


class LinkRequest(TimeStampedModel):

    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Подтверждена"
        REJECTED = "rejected", "Отклонена"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="link_requests"
    )
    athlete = models.ForeignKey(
        Athlete, on_delete=models.CASCADE, related_name="link_requests"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_link_requests",
    )

    class Meta:
        verbose_name = "Заявка на привязку профиля"
        verbose_name_plural = "Заявки на привязку профиля"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "athlete"],
                condition=Q(status="pending"),
                name="unique_pending_link_request",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.athlete} ({self.get_status_display()})"
