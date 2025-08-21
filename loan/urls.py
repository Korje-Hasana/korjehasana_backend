from django.urls import path
from .views import LoanListView, LoanListAdminView

urlpatterns = [
    path('all', LoanListView.as_view(), name="all-loan-list"),
    path('all-admin', LoanListAdminView.as_view(), name="all-loan-list-admin"),
]