from django.contrib import admin
from apps.branches.models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "phone",
        "is_published",
    )
    list_filter = ("is_published",)
    list_fields = (
        "name",
        "city",
    )


# Register your models here.
