from django.views.generic import ListView, DetailView
from apps.branches.models import Branch


class BranchListView(ListView):
    model = Branch
    template_name = "branches/branch_list.html"
    context_object_name = "branches"
    queryset = Branch.objects.filter(is_published=True)


class BranchDetailView(DetailView):
    model = Branch
    template_name = "branches/branch_detail.html"
    context_object_name = "branch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["coaches"] = self.object.coach_set.filter(is_published=True)
        return context
