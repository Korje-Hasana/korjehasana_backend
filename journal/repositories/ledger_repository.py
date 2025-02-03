from journal.models import Ledger


class LedgerRepository:
    """Repository handling database operations for Ledger."""

    @staticmethod
    def create_ledger(data):
        """Creates a new Ledger entry."""
        return Ledger.objects.create(**data)

    @staticmethod
    def get_all_ledgers():
        """Retrieves all Ledger records."""
        return Ledger.objects.all()

    @staticmethod
    def get_ledger_by_id(ledger_id):
        """Fetches a single Ledger by its code."""
        return Ledger.objects.get(id=ledger_id)