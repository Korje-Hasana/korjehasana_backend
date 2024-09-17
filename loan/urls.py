from django.urls import path
from .views import LoanListView

urlpatterns = [
    path('all', LoanListView.as_view(), name="all-loan-list")
]