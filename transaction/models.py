from datetime import date, timedelta

from django.db import models
from django.core.exceptions import ValidationError
from organization.models import BaseModel
from django.contrib.auth import get_user_model

User = get_user_model()


class TransactionLogManager(models.Manager):
    def create_transaction_log(self, amount, detail, entry1=None, entry2=None):
        self.get_queryset().create(

        )

class TransactionLog(models.Model):
    amount = models.IntegerField()
    detail = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)




SAVINGS_TRANS_TYPE = (
    ("deposit", "Deposit"),
    ("withdraw", "Withdraw"),
)

TRANSACTION_TYPE = (
    ("income", "Income"),
    ("expense", "Expense"),
)

CATEGORY_TYPES = (
    ("income", "Income"),
    ("expense", "Expense"),
)


class TransactionCategory(models.Model):
    name = models.CharField(max_length=50)
    category_type = models.CharField(
        max_length=10, choices=CATEGORY_TYPES, default="income"
    )

    def __str__(self):
        return self.name


class GeneralTransaction(BaseModel):
    amount = models.IntegerField()
    date = models.DateField()
    transaction_type = models.CharField(choices=TRANSACTION_TYPE, max_length=10)
    category = models.ForeignKey(TransactionCategory, models.PROTECT)
    summary = models.TextField(blank=True, max_length=150)

    # Cash-in-hand is derived from GeneralJournal (CA ledger) — no separate
    # snapshot table needed. The corresponding journal entries are written by
    # the API layer (see transaction.api.IncomeTransactionListCreate /
    # ExpenseTransactionListCreate calling GeneralJournal.objects.create_*_entry).


class Savings(BaseModel):
    amount = models.IntegerField()
    date = models.DateField()
    balance = models.IntegerField(default=0)
    transaction_type = models.CharField(
        max_length=10, choices=SAVINGS_TRANS_TYPE, default="deposit"
    )
    member = models.ForeignKey("peoples.Member", on_delete=models.PROTECT)
    team = models.ForeignKey("organization.Team", on_delete=models.PROTECT)

    def deposit(self):
        """balance = last balance + savings amount."""
        latest_savings = Savings.objects.filter(member=self.member).last()
        last_balance = latest_savings.balance if latest_savings else 0
        self.balance = self.amount + last_balance
        self.transaction_type = "deposit"
        self.save()

    def withdraw(self):
        """balance = last balance - withdrawal amount."""
        latest_savings = Savings.objects.filter(member=self.member).last()
        if not latest_savings:
            raise ValueError("Withdraw not possible")
        if self.amount > latest_savings.balance:
            raise ValueError("Invalid amount")
        self.balance = latest_savings.balance - self.amount
        self.transaction_type = "withdraw"
        self.save()

    class Meta:
        unique_together = ("member", "date", "transaction_type")


class LoanReason(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Loan(BaseModel):
    amount = models.IntegerField()
    date = models.DateField()
    member = models.ForeignKey("peoples.Member", on_delete=models.PROTECT)
    team = models.ForeignKey("organization.Team", on_delete=models.PROTECT)
    is_paid = models.BooleanField(default=False)
    total_installment = models.IntegerField(default=0)
    installment_paid = models.IntegerField(default=0)
    total_paid = models.IntegerField(default=0)
    total_due = models.IntegerField(default=0)
    loan_reason = models.ForeignKey(LoanReason, on_delete=models.SET_NULL, blank=True, null=True)

    # 1 installment = 1 week. First installment is due 7 days after
    # disbursement; an installment is "overdue" once 7 more days have passed
    # without payment (so installment N is overdue at day N*7 + 7).
    OVERDUE_GRACE_DAYS = 7

    def __str__(self):
        return f"Loan of {self.amount} to {self.member.name}"

    @property
    def weekly_installment(self):
        if not self.total_installment:
            return 0
        return self.amount // self.total_installment

    @property
    def final_due_date(self):
        return self.date + timedelta(weeks=self.total_installment)

    def expected_installments_by(self, as_of):
        """How many weekly installments were scheduled to have been paid by `as_of`.

        Used for the monthly collection-efficiency report. Strict schedule —
        ignores the overdue grace period. First installment is scheduled at
        loan.date + 7 days.
        """
        if as_of < self.date:
            return 0
        weeks_elapsed = (as_of - self.date).days // 7
        return min(weeks_elapsed, self.total_installment)

    def installments_overdue(self, as_of=None):
        """Number of installments past due *and* past the grace period."""
        as_of = as_of or date.today()
        graced = as_of - timedelta(days=self.OVERDUE_GRACE_DAYS)
        expected = self.expected_installments_by(graced)
        return max(0, expected - self.installment_paid)

    def is_overdue(self, as_of=None):
        return not self.is_paid and self.installments_overdue(as_of) > 0

    def amount_overdue(self, as_of=None):
        return self.installments_overdue(as_of) * self.weekly_installment

    # def clean(self):
    #     # Ensure that total_paid and total_due are consistent
    #     if self.total_paid + self.total_due != self.amount:
    #         raise ValidationError("Total paid and total due must sum up to the loan amount.")

    def pay_installment(self, payment_amount):
        """
        Update Loan status after installment submission
        """
        if self.is_paid:
            raise ValidationError("This loan is already fully paid.")

        if payment_amount > self.total_due:
            raise ValidationError("Payment amount cannot exceed the total due.")

        self.total_paid += payment_amount
        self.total_due -= payment_amount
        self.installment_paid += 1

        if self.total_paid >= self.amount and self.total_due <= 0:
            self.is_paid = True
        self.save()
        # Cash in hand calculation


class Installment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateField()

    class Meta:
        unique_together = ("loan", "date")


LOAN_REQUEST_STATUS = (
    ("pending", "Pending"),
    ("disbursed", "Disbursed"),
    ("cancelled", "Cancelled"),
)


class LoanRequest(BaseModel):
    member = models.ForeignKey("peoples.Member", on_delete=models.PROTECT)
    requested_amount = models.IntegerField(default=0)
    total_installment = models.IntegerField(default=0)
    loan_reason = models.ForeignKey(LoanReason, on_delete=models.SET_NULL, blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, default="")
    position = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=LOAN_REQUEST_STATUS, default="pending")

    class Meta:
        ordering = ("position", "id")
        indexes = [models.Index(fields=("branch", "status", "position"))]

    def __str__(self):
        return f"Request from {self.member.name} ({self.status})"
