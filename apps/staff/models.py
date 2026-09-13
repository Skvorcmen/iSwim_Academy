from django.db import models
from apps.core.models import TimeStampedModel, SEOMixin, PublicModel
from apps.branches.models import Branch


class Coach(TimeStampedModel, SEOMixin, PublicModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to="coach_photos", blank=True)
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    experience_years = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Тренер"
        verbose_name_plural = "Тренеры"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Create your models here.
