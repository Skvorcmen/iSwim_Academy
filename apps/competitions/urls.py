from django.urls import path
from apps.competitions.views import (
    DownloadTemplateView,
    UploadApplicationView,
    FormHeatsView,
    ViewHeatsView,
    EnterResultsView,
    EventResultsView,
    DownloadEventResultsPdfView,
    DownloadCompetitionResultsPdfView,
    CompetitionListView,
    ManageCompetitionView,
    CreateCompetitionView,
    DeleteEventView,
    DownloadStartProtocolPdfView,
    EditCompetitionView,
)

urlpatterns = [
    path(
        "<int:competition_id>/download-template/",
        DownloadTemplateView.as_view(),
        name="download_template",
    ),
    path(
        "<int:competition_id>/upload-application/",
        UploadApplicationView.as_view(),
        name="upload_application",
    ),
    path(
        "<int:competition_id>/form-heats/", FormHeatsView.as_view(), name="form_heats"
    ),
    path("<int:competition_id>/heats/", ViewHeatsView.as_view(), name="view_heats"),
    path(
        "heat/<int:heat_id>/enter-results/",
        EnterResultsView.as_view(),
        name="enter_results",
    ),
    path(
        "event/<int:event_id>/results/",
        EventResultsView.as_view(),
        name="event_results",
    ),
    path(
        "event/<int:event_id>/results/pdf/",
        DownloadEventResultsPdfView.as_view(),
        name="download_event_results_pdf",
    ),
    path(
        "<int:competition_id>/results/pdf/",
        DownloadCompetitionResultsPdfView.as_view(),
        name="download_competition_results_pdf",
    ),
    path("", CompetitionListView.as_view(), name="competition_list"),
    path("create/", CreateCompetitionView.as_view(), name="create_competition"),
    path(
        "<int:competition_id>/manage/",
        ManageCompetitionView.as_view(),
        name="manage_competition",
    ),
    path(
        "event/<int:event_id>/delete/", DeleteEventView.as_view(), name="delete_event"
    ),
    path(
        "<int:competition_id>/start-protocol/pdf/",
        DownloadStartProtocolPdfView.as_view(),
        name="download_start_protocol_pdf",
    ),
    path(
        "<int:competition_id>/edit/",
        EditCompetitionView.as_view(),
        name="edit_competition",
    ),
]
