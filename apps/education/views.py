from django.views.generic import ListView, DetailView
from apps.education.models import Article, ArticleCategory


class ArticleListView(ListView):
    model = Article
    template_name = "education/list.html"
    context_object_name = "articles"
    queryset = Article.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ArticleCategory.objects.all()
        context["current_category"] = self.request.GET.get("category")
        return context

    def get_queryset(self):
        queryset = Article.objects.filter(is_published=True)
        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset


class ArticleDetailView(DetailView):
    model = Article
    template_name = "education/detail.html"
    context_object_name = "article"
