from django.db.models import Sum
from transaction.models import Loan

class LoanRepository:
    @staticmethod
    def get_total_loan_count():
        return Loan.objects.count()

    @staticmethod
    def get_total_loan_amount():
        result = Loan.objects.aggregate(total_amount=Sum('amount'))
        return result['total_amount'] or 0