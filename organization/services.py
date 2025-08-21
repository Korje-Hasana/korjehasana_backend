# write service class for Organization model

from organization.models import Organization
from organization.repositories import OrganizationRepository, BranchRepository


class OrganizationService:
    def __init__(self):
        self.organization_repository = OrganizationRepository()

    def get_organization(self, pk):
        return self.organization_repository.get_organization(pk)

    def get_total_members(self, pk):
        return self.organization_repository.get_total_members(pk)

    def get_total_branches(self, pk):
        return self.organization_repository.get_total_branches(pk)



class BranchService:
    """Service for branch business logic"""

    def __init__(self):
        self.repository = BranchRepository()

    def get_branch_statistics(self):
        """Get branch statistics with proper handling of null values"""
        branches = self.repository.get_branch_statistics()

        # Process the data to handle null values and add calculated fields
        branch_stats = []
        for branch in branches:
            stats = {
                'branch': branch,
                'name': branch.name,
                'address': getattr(branch, 'address', ''),  # Handle if address field doesn't exist
                'total_member': branch.total_member or 0,
                'total_loan_count': branch.total_loan_count or 0,
            }

            branch_stats.append(stats)

        return branch_stats

    def get_overall_statistics(self):
        """Get overall statistics across all branches"""
        branch_stats = self.get_branch_statistics()

        return {
            'total_branches': len(branch_stats),
            'total_members': sum(stat['total_member'] for stat in branch_stats),
            'total_loans': sum(stat['total_loan_count'] for stat in branch_stats),
        }