from django.db.models import Q
from journal.models import GeneralJournal

class GeneralJournalRepository:
    @staticmethod
    def get_all():
        """Fetch all General Journal records"""
        return GeneralJournal.objects.all()

    @staticmethod
    def get_by_member(member_id):
        """Fetch journal entries for a specific member"""
        return GeneralJournal.objects.filter(member_id=member_id)

    @staticmethod
    def get_by_account_type_lp():
        """Fetch journal entries where account type is 'LP' (assuming 'LP' is stored in a related Ledger model)"""
        return GeneralJournal.objects.filter(accounts__account_type="LP")

    @staticmethod
    def get_member_account_payable(member_id):
        """Fetch journal entries for a specific member where account type is 'LP'"""
        return GeneralJournal.objects.filter(Q(member_id=member_id) & Q(accounts__ledger_type__code="LP")).order_by('-date')
