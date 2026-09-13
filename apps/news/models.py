from django.db import models
from apps.core.models import TimeStampedModel, SEOMixin, PublicModel
from apps.users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class News(TimeStampedModel, SEOMixin, PublicModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to="news/", blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to="news/", blank=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = " Новости"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
