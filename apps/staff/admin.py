from django.contrib import admin
from apps.staff.models import Coach


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "branch",
        "specialization",
        "is_published",
    )
    search_fields = ("first_name", "last_name")


# Register your models here.
