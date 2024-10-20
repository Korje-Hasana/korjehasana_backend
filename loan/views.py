from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Q, Sum
from transaction.models import Loan


class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'loan/loan_list.html'  # Adjust to your template path
    context_object_name = 'loans'
    paginate_by = 50  # Number of loans per page
    ordering = ['date']  # Default ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate total loan amount from the filtered queryset
        total_loan_amount = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        # Pass total_loan_amount to context
        context['total_loan'] = total_loan_amount
        return context

    def get_queryset(self):
        # Get the logged-in user's branch
        user_branch = self.request.user.branch  # Assuming User has a branch field

        # Base queryset filtering by branch
        queryset = Loan.objects.filter(member__branch=user_branch, is_paid=False).select_related('member')

        # Handle search query
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(member__name__icontains=query) |  # Assuming member has a name field
                Q(amount__icontains=query) |
                Q(date__icontains=query)
            )

        # Handle date range filtering
        startdate = self.request.GET.get('startdate', '')
        enddate = self.request.GET.get('enddate', '')
        if startdate and enddate:
            queryset = queryset.filter(date__range=[startdate, enddate])
        elif startdate:
            queryset = queryset.filter(date__gte=startdate)
        elif enddate:
            queryset = queryset.filter(date__lte=enddate)

        # Handle ordering
        order_by = self.request.GET.get('order_by', 'date')
        direction = self.request.GET.get('direction', 'asc')
        if direction == 'desc':
            order_by = f'-{order_by}'

        queryset = queryset.order_by(order_by)

        return queryset
