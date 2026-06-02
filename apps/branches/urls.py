from django.urls import path
from django.views.generic import DetailView

from apps.branches.views import BranchListView

urlpatterns = [
    path("", BranchListView.as_view(), name="branch-list"),
    path("<int:pk>/", DetailView.as_view(), name="branch-detail"),
]
