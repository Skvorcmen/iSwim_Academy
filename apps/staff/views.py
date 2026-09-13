from django.views.generic import DetailView, ListView
from apps.staff.models import Coach


class CoachListView(ListView):
    model = Coach
    template_name = "staff/coach_list.html"
    context_object_name = "coaches"
    queryset = Coach.objects.filter(is_published=True)


class CoachDetailView(DetailView):
    model = Coach
    template_name = "staff/coach_detail.html"
    context_object_name = "coach"
