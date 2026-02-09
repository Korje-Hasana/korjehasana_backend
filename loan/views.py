import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
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
        
        # Build query params string for pagination links
        query_params = []
        if self.request.GET.get('q'):
            query_params.append(f"q={self.request.GET.get('q')}")
        if self.request.GET.get('branch'):
            query_params.append(f"branch={self.request.GET.get('branch')}")
        if self.request.GET.get('startdate'):
            query_params.append(f"startdate={self.request.GET.get('startdate')}")
        if self.request.GET.get('enddate'):
            query_params.append(f"enddate={self.request.GET.get('enddate')}")
        if self.request.GET.get('order_by'):
            query_params.append(f"order_by={self.request.GET.get('order_by')}")
        if self.request.GET.get('direction'):
            query_params.append(f"direction={self.request.GET.get('direction')}")
        
        context['query_params'] = '&'.join(query_params)
        
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

    def get(self, request, *args, **kwargs):
        """Handle GET requests - check if CSV export is requested"""
        if request.GET.get('export') == 'csv':
            return self.export_to_csv()
        return super().get(request, *args, **kwargs)

    def export_to_csv(self):
        """Export loans to CSV file"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="loans_export.csv"'
        
        writer = csv.writer(response)
        
        # Get CSV rows from service
        loans = self.get_queryset()
        csv_rows = self.loan_service.generate_csv_rows(loans)
        
        # Write all rows
        writer.writerows(csv_rows)
        
        return response
