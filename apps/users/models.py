from django.contrib.auth.models import AbstractUser
from django.conf import settings
from apps.core.models import TimeStampedModel
from django.db import models
from apps.users.storage import get_private_storage


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


class RoleRequest(TimeStampedModel):

    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_requests"
    )
    diploma_scan = models.FileField(
        "Скан диплома", upload_to="diplomas/", storage=get_private_storage
    )
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    admin_comment = models.TextField("Комментарий администратора", blank=True)

    class Meta:
        verbose_name = "Заявка на роль тренера"
        verbose_name_plural = "Заявки на роль тренера"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.get_status_display()}"
