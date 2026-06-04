from django.urls import path
from apps.news.views import NewsListView, NewsDetailView

urlpatterns = [
    path("", NewsListView.as_view(), name="news-list"),
    path("slug/<slug:slug>", NewsDetailView.as_view(), name="news-detail"),
]
