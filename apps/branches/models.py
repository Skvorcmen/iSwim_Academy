from django.core.files.uploadedfile import UploadedFile
from django.db import models
from apps.core.models import TimeStampedModel, PublicModel, SEOMixin


class Branch(TimeStampedModel, PublicModel, SEOMixin):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    manager_name = models.CharField(max_length=100, blank=True)
    manager_photo = models.ImageField(upload_to="seo/manager/", blank=True)
    photo = models.ImageField(upload_to="branches/", blank=True)

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

    def __str__(self):
        return self.name
