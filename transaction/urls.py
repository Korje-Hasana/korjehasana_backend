from django.urls import path
from .views import *

urlpatterns =[
    path('', dashboard, name="dashboard"),
    path('deposits/<int:team_id>', deposit_list, name="deposit_list"),
    path('loan/list/<int:team_id>', loan_list, name="loan_list"),
    path('deposit-posting/', DepositPostingView.as_view(), name="deposit_posting"),
    path('withdraw-posting/<int:member_id>', WithdrawalPostingView.as_view(), name="withdrawal_posting"),
    path('loans/create/<int:member>', LoanDisbursementView.as_view(), name='loan_disbursement'),
    path('loans/installment/', installment_posting, name='installment_posting'),
    path('income/create', IncomeCreateView.as_view(), name='income_create'),
    path('expense/create', ExpenseCreateView.as_view(), name='expense_create'),
    path('income-expense/list', income_expense_list, name='income_list'),

]