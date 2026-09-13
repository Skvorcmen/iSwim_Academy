from django.db import models
from apps.core.models import TimeStampedModel, PublicModel, SEOMixin


class ArticleCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Article(TimeStampedModel, PublicModel, SEOMixin):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to="education/", blank=True)
    category = models.ForeignKey(
        ArticleCategory, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
