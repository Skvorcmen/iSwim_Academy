from django.urls import path
from apps.users.views import (
    RegisterView,
    ProfileView,
    ProfileEditView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path(
        "password/change/",
        UserPasswordChangeView.as_view(),
        name="user_password_change",
    ),
    path(
        "password/change/done/",
        UserPasswordChangeDoneView.as_view(),
        name="user_password_change_done",
    ),
]
