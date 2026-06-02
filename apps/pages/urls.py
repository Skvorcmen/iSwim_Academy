from django.urls import path
from apps.pages.views import HomeView, ContactsView, AboutView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
]
