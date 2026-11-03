from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from apps.users.models import User, RoleRequest


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Роль в iSwim", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Роль в iSwim", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")


@admin.action(description="Одобрить (назначить тренером)")
def approve_requests(modeladmin, request, queryset):
    count = 0
    for r in queryset.filter(status=RoleRequest.Status.PENDING).select_related("user"):
        r.user.role = "coach"
        r.user.save(update_fields=["role"])
        r.status = RoleRequest.Status.APPROVED
        r.save(update_fields=["status"])
        count += 1
    messages.success(request, f"Одобрено заявок: {count}")


@admin.action(description="Отклонить")
def reject_requests(modeladmin, request, queryset):
    queryset.filter(status=RoleRequest.Status.PENDING).update(
        status=RoleRequest.Status.REJECTED
    )


@admin.register(RoleRequest)
class RoleRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("user", "diploma_scan", "comment")
    actions = [approve_requests, reject_requests]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == RoleRequest.Status.APPROVED and obj.user.role in (
            "fan",
            "athlete",
        ):
            obj.user.role = "coach"
            obj.user.save(update_fields=["role"])
