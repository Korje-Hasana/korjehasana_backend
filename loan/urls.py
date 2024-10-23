from django.urls import path
from .views import LoanListView
from . import views 

urlpatterns = [
    path('all', LoanListView.as_view(), name="all-loan-list"),
    path('loan-reasons/', views.loan_reason_list, name='loan_reason_list'),
    path('loan-reasons/create/', views.loan_reason_create, name='loan_reason_create'),
    path('loan-reason/edit/<int:pk>/', views.loan_reason_edit, name='loan_reason_edit'),
    path('loan-reason/delete/<int:pk>/', views.loan_reason_delete, name='loan_reason_delete'),
]