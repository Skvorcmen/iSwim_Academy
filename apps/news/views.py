from multiprocessing import context
from unicodedata import category

from django.views.generic import ListView, DetailView
from apps.news.models import News, Category


class NewsListView(ListView):
    model = News
    template_name = "news/news_list.html"
    context_object_name = "news_list"
    queryset = News.objects.filter(is_published=True)
    paginate_by = 10

    def get_queryset(self):
        queryset = News.objects.filter(is_published=True)
        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_category"] = self.request.GET.get("category")
        return context


class NewsDetailView(DetailView):
    model = News
    template_name = "news/news_detail.html"
    context_object_name = "news"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_news"] = News.objects.filter(
            is_published=True, category=self.object.category
        ).exclude(pk=self.object.pk)[:3]
        return context


# Create your views here.
