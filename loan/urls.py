from django.urls import path
from .views import LoanListView
from . import views 
from .views import (
    LoanReasonListView,
    LoanReasonCreateView,
    LoanReasonUpdateView,
    LoanReasonDeleteView,
)

urlpatterns = [
    path('all', LoanListView.as_view(), name="all-loan-list"),
    path('loan-reasons/', LoanReasonListView.as_view(), name='loan_reason_list'),
    path('loan-reasons/create/', LoanReasonCreateView.as_view(), name='loan_reason_create'),
    path('loan-reasons/edit/<int:pk>/', LoanReasonUpdateView.as_view(), name='loan_reason_edit'),
    path('loan-reasons/delete/<int:pk>/', LoanReasonDeleteView.as_view(), name='loan_reason_delete'),

]