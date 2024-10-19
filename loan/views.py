from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Q
from transaction.models import Loan


class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'loan/loan_list.html'  # Adjust to your template path
    context_object_name = 'loans'
    paginate_by = 50  # Number of loans per page
    ordering = ['date']  # Default ordering

    def get_queryset(self):
        # Get the logged-in user's branch
        user_branch = self.request.user.branch  # Assuming User has a branch field

        # Base queryset filtering by branch
        queryset = Loan.objects.filter(member__branch=user_branch, is_paid=False)

        # Handle search query
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(member__name__icontains=query) |  # Assuming member has a name field
                Q(amount__icontains=query) |
                Q(date__icontains=query)
            )

        # Handle ordering
        order_by = self.request.GET.get('order_by', 'date')
        direction = self.request.GET.get('direction', 'asc')
        if direction == 'desc':
            order_by = f'-{order_by}'

        queryset = queryset.order_by(order_by)

        return queryset
