from django.urls import path
from apps.staff.views import CoachDetailView, CoachListView

urlpatterns = [
    path("", CoachListView.as_view(), name="coach_list"),
    path("<int:pk>/", CoachDetailView.as_view(), name="coach_detail"),
]
