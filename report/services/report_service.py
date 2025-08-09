# write service class here
from collections import defaultdict
from datetime import timedelta
import calendar
from datetime import date
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from collections import OrderedDict
from journal.models import GeneralJournal, Ledger
from peoples.models import Member

from django.utils.timezone import now
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from journal.models import GeneralJournal
from journal.repositories import GeneralJournalRepository
from transaction.models import Loan


class ReportService:
    def __init__(self, branch=None):
        self.branch = branch
        self.journal_repository = GeneralJournalRepository(branch=branch)

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
        return months, total_loans, total_installments

    def get_monthly_collection_percentages(self):
        today = date.today()
        year = today.year
        # 1️⃣ Get all active members
        members = Loan.objects.filter(is_paid=False, branch=self.branch)

        # 2️⃣ Received installments grouped by month
        received_qs = (
            GeneralJournal.objects.filter(
                branch=self.branch,
                accounts__code='IN',
                date__year=year,
                credit__gt=0
            )
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(received=Count('id'))
        )
        received_dict = {r['month']: r['received'] for r in received_qs}

        # 3️⃣ Calculate cumulative members per month
        result = OrderedDict()
        for month in range(1, 13):
            month_end = date(year, month, calendar.monthrange(year, month)[1])
            total_members = members.filter(created_at__lte=month_end).count()
            total_installments = total_members * 4
            received = received_dict.get(date(year, month, 1), 0)
            percentage = round((received / total_installments) * 100, 2) if total_installments else 0
            result[calendar.month_abbr[month]] = percentage

        return result
