from django.urls import path
from apps.branches.views import BranchListView, BranchDetailView

urlpatterns = [
    path("", BranchListView.as_view(), name="branch-list"),
    path("<int:pk>/", BranchDetailView.as_view(), name="branch-detail"),
]
