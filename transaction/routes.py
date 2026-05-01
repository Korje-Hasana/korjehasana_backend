from django.urls import path
from .dashboard_views import *

from django.urls import path
from . import api as views

app_name = 'transaction'

urlpatterns = [
    path('deposit/', views.DepositView.as_view()),
    path('deposit-bulk/', views.DepositBulkView.as_view(), name='deposit_bulk'),
    path('withdraw/', views.WithdrawView.as_view()),
    # Both spellings for backwards compatibility (web uses 'disbursment').
    path('loan-disbursement/', views.LoanDisbursementView.as_view(), name='loan_disbursement'),
    path('loan-disbursment/', views.LoanDisbursementView.as_view()),
    path('loan-installment/', views.LoanInstallmentView.as_view()),
    path('installment-bulk/', views.InstallmentBulkView.as_view(), name='installment_bulk'),
    path('finance-summary/', views.FinanceSummaryView.as_view(), name='finance_summary'),
    path('member-savings-list', views.MemberSavingsData.as_view()),
    path('member-installment-list', views.MemberLoanData.as_view()),
    path('income/', views.IncomeTransactionListCreate.as_view(), name='income_create_list'),
    path('income/<int:id>/', views.IncomeTransactionDetailUpdateDelete.as_view(), name='income_re_up_del'),
    path('expense/', views.ExpenseTransactionListCreate.as_view(), name='expense_create_list'),
    path('expense/<int:id>/', views.ExpenseTransactionDetailUpdateDelete.as_view(), name='expense_re_up_del'),
    path('transaction-category-list/', views.TransactionCategoryList.as_view(), name='transaction_category_list'),
    path('loan-request/', views.LoanRequestListCreate.as_view(), name='loan_request_list_create'),
    path('loan-request/reorder/', views.LoanRequestReorder.as_view(), name='loan_request_reorder'),
    path('loan-request/<int:pk>/', views.LoanRequestDetail.as_view(), name='loan_request_detail'),
    path('loan-request/<int:pk>/disburse/', views.LoanRequestMarkDisbursed.as_view(), name='loan_request_disburse'),
]
