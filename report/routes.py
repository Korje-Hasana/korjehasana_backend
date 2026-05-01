from django.urls import path
from . import api as views

app_name = "report"

urlpatterns = [
    path("branch-summary/", views.BranchSummaryView.as_view(), name="branch_summary"),
    path("kpis/", views.KpisView.as_view(), name="kpis"),
    path("monthly/", views.MonthlyView.as_view(), name="monthly"),
    path("loans/", views.LoansListView.as_view(), name="loans_list"),
    path("overdue-loans/", views.OverdueLoansView.as_view(), name="overdue_loans"),
    path("top-borrowers/", views.TopBorrowersView.as_view(), name="top_borrowers"),
    path("top-savers/", views.TopSaversView.as_view(), name="top_savers"),
    path("team-stats/", views.TeamStatsView.as_view(), name="team_stats"),
]
