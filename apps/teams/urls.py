from django.urls import path
from apps.teams.views import (
    AthleteSearchView,
    LinkRequestCreateView,
    CoachLinkRequestsView,
    LinkRequestReviewView,
)

urlpatterns = [
    path("find-me/", AthleteSearchView.as_view(), name="athlete_search"),
    path(
        "link/<int:athlete_id>/",
        LinkRequestCreateView.as_view(),
        name="link_request_create",
    ),
    path("link-requests/", CoachLinkRequestsView.as_view(), name="coach_link_requests"),
    path(
        "link-requests/<int:pk>/<str:action>/",
        LinkRequestReviewView.as_view(),
        name="link_request_review",
    ),
]
