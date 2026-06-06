from django.urls import path
from apps.education.views import EducationProgramListView, EducationProgramDetailView

urlpatterns = [
    path("", EducationProgramListView.as_view(), name="education_program_list"),
    path(
        "<slug:slug>/",
        EducationProgramDetailView.as_view(),
        name="education_program_detail",
    ),
]
