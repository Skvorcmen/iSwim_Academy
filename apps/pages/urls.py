from django.urls import path
from apps.pages.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
