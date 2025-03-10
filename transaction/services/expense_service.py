from journal.repositories import GeneralJournalRepository
from journal.repositories.ledger_repository import LedgerRepository

class ExpenseService:
    def __init__(self, branch):
        self.general_journal_repository = GeneralJournalRepository(branch=branch)
        self.account_repository = LedgerRepository()
        self.branch = branch

    def create_expense(self, form_data):
        account = form_data['expense_type']
        date = form_data['date']
        amount = form_data['amount']
        return self.general_journal_repository.create_expense_entry(
            account=account,
            date=date,
            amount=amount,
            branch=self.branch,
            remarks=f"Expense: {account.name}"
        )

    def get_all_expenses(self):
        return self.general_journal_repository.get_all_expenses()