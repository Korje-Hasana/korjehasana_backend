from django.shortcuts import get_object_or_404, render

from organization.models import Organization
from organization.services import OrganizationService


def org_detail(request, pk):
    service = OrganizationService()

    return render(request, 'org/public_org_detail.html', {'org': org})