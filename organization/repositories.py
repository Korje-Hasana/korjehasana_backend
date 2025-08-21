from organization.models import Organization
from peoples.models import Member


class OrganizationRepository:
    def get_organization(self, pk):
        return Organization.objects.get(pk=pk)

    def get_total_members(self, pk):
        org = self.get_organization(pk)
        return Member.objects.filter(branch__organization=org).count()

    def get_total_branches(self, pk):
        org = self.get_organization(pk)
        return org.branches.count()


# repositories.py (add to existing file)
from django.db.models import Count, Sum
from .models import Branch
from transaction.models import Loan
from peoples.models import Member  # Adjust imports as needed


class BranchRepository:
    """Repository for branch data access"""

    @staticmethod
    def get_all_branches():
        return Branch.objects.filter(is_active=True).order_by('name')

    @staticmethod
    def get_branch_statistics():
        """Get comprehensive branch statistics"""
        return Branch.objects.annotate(
            # Count total members in each branch
            total_member=Count('member', distinct=True),

            # Count total loans in each branch
            total_loan_count=Count('member__loan', distinct=True),
        ).order_by('name')