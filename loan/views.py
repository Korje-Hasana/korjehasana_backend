from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Q
from transaction.models import Loan
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import LoanReason
from .forms import LoanReasonForm
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


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
    
 
# List View for LoanReason
class LoanReasonListView(LoginRequiredMixin, ListView):
    model = LoanReason
    template_name = 'loan/loan_reason_list.html'
    context_object_name = 'reasons'

# Create View for LoanReason
class LoanReasonCreateView(LoginRequiredMixin, CreateView):
    model = LoanReason
    form_class = LoanReasonForm
    template_name = 'loan/loan_reason_form.html'
    success_url = reverse_lazy('loan_reason_list')

    
# Update View for LoanReason
class LoanReasonUpdateView(LoginRequiredMixin, UpdateView):
    model = LoanReason
    form_class = LoanReasonForm
    template_name = 'loan/loan_reason_update.html'
    success_url = reverse_lazy('loan_reason_list')

# Delete View for LoanReason
class LoanReasonDeleteView(LoginRequiredMixin, DeleteView):
    model = LoanReason
    template_name = 'loan/loan_reason_confirm_delete.html'
    success_url = reverse_lazy('loan_reason_list')
    context_object_name = 'reason'
         
    
        
        
            
            
            


