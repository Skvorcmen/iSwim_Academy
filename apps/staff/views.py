from django.views.generic import DetailView, ListView
from apps.branches.models import Branch
from apps.staff.models import Coach


class CoachListView(ListView):
    model = Coach
    template_name = "staff/coach_list.html"
    context_object_name = "coaches"

    def get_queryset(self):
        qs = Coach.objects.filter(is_published=True).select_related("branch")
        branch_id = self.request.GET.get("branch", "").strip()
        if branch_id.isdigit():
            qs = qs.filter(branch_id=int(branch_id))
        return qs.order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["branches"] = Branch.objects.filter(is_published=True).order_by(
            "city", "name"
        )
        branch_id = self.request.GET.get("branch", "").strip()
        context["current_branch"] = int(branch_id) if branch_id.isdigit() else None
        return context


class CoachDetailView(DetailView):
    model = Coach
    template_name = "staff/coach_detail.html"
    context_object_name = "coach"
    queryset = Coach.objects.select_related("branch")
