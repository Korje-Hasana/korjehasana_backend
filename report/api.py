"""Read-only report endpoints used by the mobile dashboard / reports tab.

All views are scoped to `request.user.branch`. They are designed for low
latency on a single branch (≤ a few hundred members), so they prefer
aggregate SQL over Python loops where possible.
"""
from collections import OrderedDict
from datetime import date, timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from journal.models import GeneralJournal
from peoples.models import Member
from organization.models import Team
from transaction.models import GeneralTransaction, Loan


def _parse_date(raw, default):
    if not raw:
        return default
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return default


def _ledger_amount(branch, code, field, **filters):
    """Sum debit or credit on a journal account for a branch (with extra filters)."""
    return (
        GeneralJournal.objects.filter(branch=branch, accounts__code=code, **filters)
        .aggregate(s=Sum(field))["s"]
        or 0
    )


class BranchSummaryView(APIView):
    """Cash-in-hand + today/month totals for the dashboard card."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        today = _parse_date(request.query_params.get("date"), date.today())
        month_start = today.replace(day=1)

        # Cash-in-hand = lifetime CA debit - CA credit on this branch.
        cash_debit = _ledger_amount(branch, "CA", "debit")
        cash_credit = _ledger_amount(branch, "CA", "credit")
        cash_in_hand = cash_debit - cash_credit

        def at(code, field, **filters):
            return _ledger_amount(branch, code, field, **filters)

        deposit_today_total = at("DE", "credit", date=today)
        deposit_today_count = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="DE", date=today
            ).count()
        )
        installment_today_total = at("IN", "credit", date=today)
        installment_today_count = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="IN", date=today
            ).count()
        )
        disbursement_today_total = at("LO", "debit", date=today)
        disbursement_today_count = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="LO", date=today
            ).count()
        )
        withdraw_today_total = at("WI", "debit", date=today)
        withdraw_today_count = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="WI", date=today
            ).count()
        )

        deposit_month_total = at("DE", "credit", date__gte=month_start)
        installment_month_total = at("IN", "credit", date__gte=month_start)
        disbursement_month_total = at("LO", "debit", date__gte=month_start)

        return Response(
            {
                "date": today.isoformat(),
                "cash_in_hand": cash_in_hand,
                "today": {
                    "deposit_total": deposit_today_total,
                    "deposit_count": deposit_today_count,
                    "installment_total": installment_today_total,
                    "installment_count": installment_today_count,
                    "disbursement_total": disbursement_today_total,
                    "disbursement_count": disbursement_today_count,
                    "withdraw_total": withdraw_today_total,
                    "withdraw_count": withdraw_today_count,
                },
                "month_to_date": {
                    "deposit_total": deposit_month_total,
                    "installment_total": installment_month_total,
                    "disbursement_total": disbursement_month_total,
                },
            }
        )


class KpisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        members = Member.active_objects.filter(branch=branch)
        active_loans = Loan.objects.filter(branch=branch, is_paid=False)
        all_loans = Loan.objects.filter(branch=branch)

        total_savings = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="DE"
            ).aggregate(s=Sum("credit"))["s"]
            or 0
        ) - (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="WI"
            ).aggregate(s=Sum("debit"))["s"]
            or 0
        )
        total_outstanding = active_loans.aggregate(s=Sum("total_due"))["s"] or 0
        total_disbursed_lifetime = all_loans.aggregate(s=Sum("amount"))["s"] or 0
        total_collected_lifetime = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="IN"
            ).aggregate(s=Sum("credit"))["s"]
            or 0
        )

        return Response(
            {
                "total_members": members.count(),
                "active_members": members.count(),
                "active_loans_count": active_loans.count(),
                "total_savings": max(total_savings, 0),
                "total_outstanding_loan": total_outstanding,
                "total_disbursed_lifetime": total_disbursed_lifetime,
                "total_collected_lifetime": total_collected_lifetime,
            }
        )


class MonthlyView(APIView):
    """Monthly disbursement vs collection (last N months, default 6)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        try:
            months = max(1, min(int(request.query_params.get("months") or 6), 24))
        except (TypeError, ValueError):
            months = 6

        today = date.today()
        # First day of (today.month - months + 1)
        year = today.year
        month_idx = today.month - months
        while month_idx <= 0:
            month_idx += 12
            year -= 1
        start = date(year, month_idx, 1)

        # Aggregate disbursements (LO debit) and installments (IN credit) per month.
        disburse_qs = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="LO", date__gte=start
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(s=Sum("debit"))
        )
        collect_qs = (
            GeneralJournal.objects.filter(
                branch=branch, accounts__code="IN", date__gte=start
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(s=Sum("credit"))
        )

        disburse_map = {row["month"].strftime("%Y-%m"): row["s"] or 0 for row in disburse_qs}
        collect_map = {row["month"].strftime("%Y-%m"): row["s"] or 0 for row in collect_qs}

        results = []
        # Iterate forward through `months` months
        cur_year, cur_month = start.year, start.month
        for _ in range(months):
            key = f"{cur_year:04d}-{cur_month:02d}"
            disb = disburse_map.get(key, 0)
            coll = collect_map.get(key, 0)
            pct = round((coll / disb) * 100) if disb else 0
            results.append(
                {
                    "month": key,
                    "disbursement": disb,
                    "collection": coll,
                    "collection_percent": min(pct, 100),
                }
            )
            cur_month += 1
            if cur_month > 12:
                cur_month = 1
                cur_year += 1
        return Response(results)


class TopBorrowersView(APIView):
    """Members with the largest outstanding due (active loans only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        try:
            limit = max(1, min(int(request.query_params.get("limit") or 10), 50))
        except (TypeError, ValueError):
            limit = 10

        loans = (
            Loan.objects.filter(branch=branch, is_paid=False)
            .select_related("member", "team")
            .order_by("-total_due")[:limit]
        )

        out = []
        for loan in loans:
            m = loan.member
            out.append(
                {
                    "id": m.id,
                    "name": m.name,
                    "guardian_name": m.guardian_name,
                    "team_name": loan.team.name if loan.team else (m.team.name if m.team else ""),
                    "serial_number": m.serial_number,
                    "loan_amount": loan.amount,
                    "total_due": loan.total_due,
                    "installment_paid": loan.installment_paid,
                    "total_installment": loan.total_installment,
                }
            )
        return Response(out)


class TopSaversView(APIView):
    """Members with the highest savings balance (sum of DE credit - WI debit)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        try:
            limit = max(1, min(int(request.query_params.get("limit") or 10), 50))
        except (TypeError, ValueError):
            limit = 10

        # Aggregate per-member balance from journal in a single query.
        deposits = (
            GeneralJournal.objects.filter(branch=branch, accounts__code="DE")
            .values("member_id")
            .annotate(deposit=Sum("credit"))
        )
        withdraws = (
            GeneralJournal.objects.filter(branch=branch, accounts__code="WI")
            .values("member_id")
            .annotate(withdraw=Sum("debit"))
        )
        deposit_map = {row["member_id"]: row["deposit"] or 0 for row in deposits}
        withdraw_map = {row["member_id"]: row["withdraw"] or 0 for row in withdraws}

        balances = []
        for member_id, dep in deposit_map.items():
            balance = dep - withdraw_map.get(member_id, 0)
            if balance > 0:
                balances.append((member_id, balance))
        balances.sort(key=lambda r: r[1], reverse=True)
        balances = balances[:limit]

        member_ids = [b[0] for b in balances]
        members = (
            Member.active_objects.filter(id__in=member_ids, branch=branch)
            .select_related("team")
        )
        member_map = {m.id: m for m in members}

        out = []
        for member_id, balance in balances:
            m = member_map.get(member_id)
            if not m:
                continue
            out.append(
                {
                    "id": m.id,
                    "name": m.name,
                    "guardian_name": m.guardian_name,
                    "team_name": m.team.name if m.team else "",
                    "serial_number": m.serial_number,
                    "savings_balance": balance,
                }
            )
        return Response(out)


class TeamStatsView(APIView):
    """Per-team aggregates for the user's branch."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        teams = Team.objects.filter(branch=branch).order_by("name")
        out = []
        for team in teams:
            member_count = team.members.filter(is_active=True).count()
            active_loans = Loan.objects.filter(team=team, is_paid=False)
            outstanding = active_loans.aggregate(s=Sum("total_due"))["s"] or 0
            savings = (
                GeneralJournal.objects.filter(
                    member__team=team, accounts__code="DE"
                ).aggregate(s=Sum("credit"))["s"]
                or 0
            ) - (
                GeneralJournal.objects.filter(
                    member__team=team, accounts__code="WI"
                ).aggregate(s=Sum("debit"))["s"]
                or 0
            )
            out.append(
                {
                    "team_id": team.id,
                    "team_name": team.name,
                    "member_count": member_count,
                    "active_loan_count": active_loans.count(),
                    "total_savings": max(savings, 0),
                    "total_outstanding": outstanding,
                }
            )
        return Response(out)
