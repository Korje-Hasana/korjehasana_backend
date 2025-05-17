# write service class for Organization model

from organization.models import Organization
from organization.repositories import OrganizationRepository


class OrganizationService:
    def __init__(self):
        self.organization_repository = OrganizationRepository()

    def get_organization(self, pk):
        return self.organization_repository.get_organization(pk)

    def get_total_members(self, pk):
        return self.organization_repository.get_total_members(pk)

    def get_total_branches(self, pk):
        return self.organization_repository.get_total_branches(pk)

