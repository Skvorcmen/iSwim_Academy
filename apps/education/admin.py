from django.contrib import admin
from apps.education.models import Article, ArticleCategory


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "created_at", "is_published"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}
