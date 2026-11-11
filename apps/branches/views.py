from django.db.models import Count, Q
from django.views.generic import ListView, DetailView
from apps.branches.models import Branch


class BranchListView(ListView):
    model = Branch
    template_name = "branches/branch_list.html"
    context_object_name = "branches"

    def get_queryset(self):
        qs = (
            Branch.objects.filter(is_published=True)
            .annotate(
                coaches_count=Count(
                    "coach", filter=Q(coach__is_published=True), distinct=True
                )
            )
            .order_by("city", "name")
        )
        city = self.request.GET.get("city", "").strip()
        if city:
            qs = qs.filter(city=city)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cities"] = (
            Branch.objects.filter(is_published=True)
            .order_by("city")
            .values_list("city", flat=True)
            .distinct()
        )
        context["current_city"] = self.request.GET.get("city", "").strip()
        return context


class BranchDetailView(DetailView):
    model = Branch
    template_name = "branches/branch_detail.html"
    context_object_name = "branch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["coaches"] = self.object.coach_set.filter(is_published=True)
        return context
