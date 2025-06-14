from django.db.models import Q, Sum
from journal.models import GeneralJournal, Ledger

class GeneralJournalRepository:
    def __init__(self, branch=None):
        self.branch = branch

    def cash_credit(self, date, member, amount, branch, remarks=""):
        cash_account = Ledger.objects.get(code='CA')
        entry = GeneralJournal.objects.create(
            date=date,
            member=member,
            accounts=cash_account,
            branch=branch,
            credit=amount,
            remarks=remarks
        )
        return entry

    def cash_debit(self, date, member, amount, branch, remarks):
        cash_account = Ledger.objects.get(code='CA')
        entry = GeneralJournal.objects.create(
            date=date,
            member=member,
            accounts=cash_account,
            branch=branch,
            debit=amount,
            remarks=remarks
        )
        return entry


    def create_income_entry(self, account, date, branch, amount, remarks=""):
        GeneralJournal.objects.create(
            date=date,
            accounts=account,
            branch=branch,
            credit=amount,
            remarks=remarks
        )
        self.cash_debit(date=date, member=None, amount=amount, branch=branch, remarks=remarks)

    def create_expense_entry(self, account, date, branch, amount, remarks=""):
        GeneralJournal.objects.create(
            date=date,
            accounts=account,
            branch=branch,
            debit=amount,
            remarks=remarks
        )
        self.cash_credit(date=date, member=None, amount=amount, branch=branch, remarks=remarks)

    def get_all_incomes(self):
        return GeneralJournal.objects.filter(branch=self.branch, accounts__ledger_type__code='OI') # OI = Owner Equity Income

    # update get_all_incomes function to get sum of all incomes
    def get_income_total(self):
        return GeneralJournal.objects.filter(branch=self.branch, accounts__ledger_type__code='OI').aggregate(Sum('credit'))['credit__sum']

    # update get_all_incomes function to get sum of all expenses
    def get_expense_total(self):
        return GeneralJournal.objects.filter(branch=self.branch, accounts__ledger_type__code='OE').aggregate(Sum('debit'))['debit__sum']

    def get_all_expenses(self):
        return GeneralJournal.objects.filter(branch=self.branch, accounts__ledger_type__code='OE') # OI = Owner Equity Income

    def get_member_account_payable(self, member_id):
        """Fetch journal entries for a specific member where account type is 'LP'"""
        return GeneralJournal.objects.filter(Q(member_id=member_id) & Q(accounts__ledger_type__code="LP")).order_by('-date')


    def get_monthly_loan_installment(self, member_id, month, year):
        """Fetch journal entries for a specific member where account type is 'LP'"""
        return GeneralJournal.objects.filter(Q(member_id=member_id) & Q(accounts__ledger_type__code="LP") & Q(date__month=month) & Q(date__year=year)).order_by('-date')


    def get_member_installment(self, member_id):
        """Fetch journal entries for a specific member where account type is 'IN' (Installment Ledger)"""
        return GeneralJournal.objects.filter(Q(member_id=member_id) & Q(accounts__code='IN')).order_by('-date')

