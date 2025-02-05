# create service class to handle member transaction
from journal.repositories import GeneralJournalRepository, LedgerRepository


class MemberService:
    def __init__(self, branch):
        self.general_journal_repository = GeneralJournalRepository(branch=branch)
        self.account_repository = LedgerRepository()
        self.branch = branch

    # create function to get all transaction of a  member (deposit, withdraw)
    def get_member_transactions(self, member_id):
        return self.general_journal_repository.get_member_account_payable(member_id)