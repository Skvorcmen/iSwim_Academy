from django.contrib import admin, messages
from apps.teams.models import Team, Athlete, LinkRequest


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "coach"]
    search_fields = ["name", "city"]


@admin.action(description="Снять привязку профиля")
def unlink_profile(modeladmin, request, queryset):
    count = queryset.filter(user__isnull=False).update(user=None)
    messages.success(request, f"Привязок снято: {count}")


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = [
        "last_name",
        "first_name",
        "birth_year",
        "gender",
        "team",
        "coach",
        "user",
    ]
    list_filter = ["gender", "team"]
    search_fields = ["last_name", "first_name"]
    autocomplete_fields = ["user"]
    actions = [unlink_profile]


@admin.register(LinkRequest)
class LinkRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "athlete", "status", "reviewed_by", "created_at"]
    list_filter = ["status"]
    readonly_fields = ["user", "athlete", "reviewed_by"]
