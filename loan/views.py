from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from organization.models import Branch
from transaction.models import Loan
from .services import LoanService


class BaseLoanListView(LoginRequiredMixin, ListView):
    """Base view for loan lists"""
    model = Loan
    template_name = 'loan/loan_list.html'
    context_object_name = 'loans'
    paginate_by = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loan_service = LoanService()

    def get_search_params(self):
        """Extract search parameters from request"""
        return {
            'q': self.request.GET.get('q', ''),
            'startdate': self.request.GET.get('startdate', ''),
            'enddate': self.request.GET.get('enddate', ''),
            'order_by': self.request.GET.get('order_by', 'date'),
            'direction': self.request.GET.get('direction', 'desc'),
            'branch': self.request.GET.get('branch', ''),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_loan_amount = self.loan_service.calculate_total_loan_amount(
            self.get_queryset()
        )
        context['total_loan'] = total_loan_amount
        return context


class LoanListView(BaseLoanListView):
    """User loan list view - filtered by user's branch"""

    def get_queryset(self):
        search_params = self.get_search_params()
        return self.loan_service.get_user_loans(self.request.user, search_params)


class LoanListAdminView(BaseLoanListView):
    """Admin loan list view - shows all loans"""
    template_name = 'loan/loan_list_admin.html'  # Different template if needed

    def get_queryset(self):
        search_params = self.get_search_params()
        return self.loan_service.get_admin_loans(search_params)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['branches'] = Branch.objects.filter(is_active=True).order_by('-id')

        return context
