from django.views.generic import TemplateView
from apps.news.models import News
from apps.branches.models import Branch
from apps.staff.models import Coach
from apps.education.models import Article


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        latest_news = News.objects.filter(is_published=True).order_by("-created_at")[:3]
        branches = Branch.objects.filter(is_published=True)
        coaches = Coach.objects.filter(is_published=True)
        articles = Article.objects.filter(is_published=True)

        context["latest_news"] = latest_news
        context["branches"] = branches
        context["branches_count"] = branches.count()
        context["coaches"] = coaches[:4]
        context["coaches_count"] = coaches.count()
        context["articles"] = articles[:3]
        context["articles_count"] = articles.count()

        return context


class ContactsView(TemplateView):
    template_name = "pages/contacts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["branches"] = Branch.objects.filter(is_published=True)
        return context


class AboutView(TemplateView):
    template_name = "pages/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["branches_count"] = Branch.objects.filter(is_published=True).count()
        context["coaches_count"] = Coach.objects.filter(is_published=True).count()
        return context
