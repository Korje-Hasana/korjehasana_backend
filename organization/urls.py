from django.urls import path
from .views import *
from .public_views import org_detail

urlpatterns = [
    path("<int:pk>/", org_detail, name="organization_detail"),
    path("dashboard/teams", team_list, name="team_list"),
    path("dashboard/teams/create", team_create, name="team_create"),
    path('dashboard/admin/branch-statistics/', BranchStatisticsView.as_view(), name='branch_statistics')
]