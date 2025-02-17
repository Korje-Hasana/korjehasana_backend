# write service class here
from collections import defaultdict
from datetime import timedelta

from django.utils.timezone import now
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from journal.models import GeneralJournal
from journal.repositories import GeneralJournalRepository

class ReportService:
    def __init__(self):
        self.journal_repository = GeneralJournalRepository()

    def get_monthly_loan_installment_report(self, branch):
        # Get the date 12 months ago from today
        twelve_months_ago = now().replace(day=1) - timedelta(days=365)
        # Query GeneralJournal for Loan (code = "LO")
        loan_data = (
            GeneralJournal.objects
            .filter(branch=branch, accounts__ledger_type__code="AR", date__gte=twelve_months_ago)  # Filter Account Receivable
            .annotate(month=TruncMonth('date'))  # Extract Month
            .values('month')
            .annotate(
                total_loan=Sum('debit'),  # Sum of loan amounts (debit)
                total_installment=Sum('credit')  # Sum of installment payments (credit)
            )
            .order_by('-month')
        )
        print(loan_data)

        # Convert to dictionary for visualization
        dataset = defaultdict(lambda: {"total_loan": 0, "total_installment": 0})

        for entry in loan_data:
            month = entry["month"].strftime("%Y-%m")  # Format as YYYY-MM
            dataset[month]["total_loan"] = entry["total_loan"] or 0
            dataset[month]["total_installment"] = entry["total_installment"] or 0

        # Convert to lists for Chart.js
        months = list(dataset.keys())
        total_loans = [data["total_loan"] for data in dataset.values()]
        total_installments = [data["total_installment"] for data in dataset.values()]
        print(total_installments)
        return months, total_loans, total_installments