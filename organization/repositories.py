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

