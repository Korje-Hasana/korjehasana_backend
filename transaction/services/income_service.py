from journal.repositories import GeneralJournalRepository
from journal.repositories.ledger_repository import LedgerRepository


class IncomeService:
    def __init__(self, branch):
        self.general_journal_repository = GeneralJournalRepository(branch=branch)
        self.account_repository = LedgerRepository()
        self.branch = branch

    def create_income(self, form_data):
        account = form_data['income_type']
        date = form_data['date']
        amount = form_data['amount']

        return self.general_journal_repository.create_income_entry(
            account=account,
            date=date,
            amount=amount,
            branch=self.branch,
            remarks=f"Income: {account.name}"
        )

    # create function to get all income from respository
    def get_all_incomes(self):
        return self.general_journal_repository.get_all_incomes()

