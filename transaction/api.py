from datetime import date as date_cls, datetime

from django.db import transaction as db_transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
)

from journal.models import GeneralJournal
from peoples.models import Member
from peoples.permissions import IsSameBranch
from .models import GeneralTransaction, Installment, Loan, Savings, TransactionCategory
from .serializers import (
    GeneralTransactionSerializer,
    DepositSerializer,
    LoanDisbursementSerializer,
    LoanInstallmentSerializer,
    TransactionCategorySerializer,
)
from .utils import format_savings_date, format_loan_data
from korjo_soft.permissions import IsBranchOwner


class DepositView(APIView):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated, IsSameBranch]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.validated_data["member"]
        date = serializer.validated_data["date"]
        amount = serializer.validated_data["amount"]
        # check member already have deposit
        already_deposited = GeneralJournal.objects.is_already_deposited(date, member, amount)
        if already_deposited:
            return Response(
                {"detail": "এই তারিখে এই পরিমাণ ইতিমধ্যে জমা আছে।"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        GeneralJournal.objects.deposit_entry(date, member, amount)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WithdrawView(APIView):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated, IsSameBranch]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.validated_data["member"]
        date = serializer.validated_data["date"]
        amount = serializer.validated_data["amount"]

        GeneralJournal.objects.create_withdraw_entry(date, member, amount)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoanDisbursementView(APIView):
    """
    Member Loan Disbursement
    """

    serializer_class = LoanDisbursementSerializer
    permission_classes = [IsAuthenticated, IsSameBranch]

    def post(self, request):
        serializer = LoanDisbursementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        date = serializer.validated_data["date"]
        member = serializer.validated_data["member"]
        amount = serializer.validated_data["amount"]
        # check member already have unpaid loan
        unpaid_loan = Loan.objects.filter(member=member, is_paid=False).exists()
        if unpaid_loan:
            return Response(
                {"detail": "এই সদস্যের চলমান কর্জ আছে।"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        loan = serializer.save(
            amount=amount,
            total_due=amount,  # full principal is due at disbursement
            branch=request.user.branch,
            team=member.team,
            created_by=request.user,
        )
        GeneralJournal.objects.create_loan_entry(date, member, amount)
        return Response({"status": "success", "id": loan.id}, status=201)


class LoanInstallmentView(APIView):
    serializer_class = LoanInstallmentSerializer
    permission_classes = [IsAuthenticated, IsSameBranch]

    def post(self, request):
        serializer = LoanInstallmentSerializer(data=request.data)
        if serializer.is_valid():
            installment = serializer.save()
            loan_object = installment.loan
            date = serializer.validated_data["date"]
            amount = serializer.validated_data["amount"]
            # Update loan status
            loan_object.pay_installment(amount)
            # Update Journal
            GeneralJournal.objects.create_installment_entry(date, loan_object.member, amount)
            return Response({"status": "success"}, status=201)
        return Response({"status": "failed", "message": serializer.errors}, status=400)


class MemberSavingsData(APIView):
    """
    [{
        "sl": 1,
        "member_id": 1,
        "member_name": "Harun",
        "guardian_name": "Sadrul Islam",
        "balance": 0,
        "week1": 0,
        "week2": 0,
        "week3": 0,
        "week4": 0
    }
    ]
    """

    def get(self, request):
        team_id = self.request.query_params.get("teamId")
        data = []
        month = self.request.query_params.get("month", datetime.today().month)
        team = self.request.query_params.get("team", None)
        # staff_branch = request.user.branch
        # members = Member.objects.filter(branch=staff_branch)
        members = Member.active_objects.filter(team__id=team_id).order_by("serial_number")

        # TODO: If not needed, remove this if
        if team:
            members = members.filter(team=team)
        for member in members:
            savings_data = format_savings_date(member, month)
            data.append(savings_data)
        return Response(data)


class MemberLoanData(APIView):
    """
    [
    {
        "sl": 1,
        "member_id": 1,
        "member_name": "Harun",
        "guardian_name": "Test",
        "loan_id": 1,
        "loan_amount": 5000,
        "loan_balance": 2000,
        "week1": 500,
        "week2": 300,
        "week3": 0,
        "week4": 0
    }
    ]
    """

    def get(self, request):
        data = []
        month = self.request.query_params.get("month", datetime.today().month)
        team = self.request.query_params.get("team", None)
        staff_branch = request.user.branch
        active_loans = Loan.objects.filter(
            branch=staff_branch, is_paid=False
        ).select_related("member").order_by("member__serial_number")

        if team:
            active_loans = active_loans.filter(team=team)
        for loan in active_loans:
            installment_data = format_loan_data(loan, month)
            data.append(installment_data)
        return Response(data)


class IncomeTransactionListCreate(ListCreateAPIView):
    serializer_class = GeneralTransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(transaction_type="income", branch=user.branch)
        data = serializer.validated_data
        category = data["category"].name
        remark = data.get("summary", "") or ""
        GeneralJournal.objects.create_income_entry(
            date=data["date"],
            branch=user.branch,
            amount=data["amount"],
            remarks=f"{category}: {remark}".strip(": "),
        )

    def get_queryset(self):
        return GeneralTransaction.objects.filter(
            transaction_type="income", branch=self.request.user.branch
        ).select_related("category").order_by("-date", "-id")


class IncomeTransactionDetailUpdateDelete(RetrieveUpdateDestroyAPIView):
    serializer_class = GeneralTransactionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        obj = get_object_or_404(GeneralTransaction, id=self.kwargs.get("id"))
        if obj.branch_id != self.request.user.branch_id:
            self.permission_denied(self.request)
        return obj


class ExpenseTransactionListCreate(ListCreateAPIView):
    serializer_class = GeneralTransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(transaction_type="expense", branch=user.branch)
        data = serializer.validated_data
        category = data["category"].name
        remark = data.get("summary", "") or ""
        GeneralJournal.objects.create_expense_entry(
            date=data["date"],
            branch=user.branch,
            amount=data["amount"],
            remarks=f"{category}: {remark}".strip(": "),
        )

    def get_queryset(self):
        return GeneralTransaction.objects.filter(
            transaction_type="expense", branch=self.request.user.branch
        ).select_related("category").order_by("-date", "-id")


class ExpenseTransactionDetailUpdateDelete(RetrieveUpdateDestroyAPIView):
    serializer_class = GeneralTransactionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        obj = get_object_or_404(GeneralTransaction, id=self.kwargs.get("id"))
        if obj.branch_id != self.request.user.branch_id:
            self.permission_denied(self.request)
        return obj


class TransactionCategoryList(ListAPIView):
    serializer_class = TransactionCategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = TransactionCategory.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category_type"]
    pagination_class = None

    def get_queryset(self):
        # Mobile passes ?kind=income|expense for naming-consistency with the
        # client. Normalize to the model's category_type.
        qs = TransactionCategory.objects.all().order_by("category_type", "name")
        kind = self.request.query_params.get("kind")
        if kind in {"income", "expense"}:
            qs = qs.filter(category_type=kind)
        return qs


class _BulkBaseView(APIView):
    """Shared bulk-transaction skeleton.

    Subclass implements `process_item(branch, date, item)` which returns a
    dict shaped `{member, status, id?, error?}`. The base view aggregates
    results, returning 201 if all succeed or 207 (Multi-Status) on partial
    failure.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        branch = request.user.branch
        if not branch:
            return Response({"detail": "User has no branch"}, status=400)

        items = request.data.get("items") or []
        date = request.data.get("date") or date_cls.today().isoformat()
        if not isinstance(items, list) or not items:
            return Response({"detail": "items must be a non-empty list"}, status=400)

        results = []
        with db_transaction.atomic():
            for item in items:
                try:
                    results.append(self.process_item(branch=branch, date=date, item=item))
                except Exception as exc:  # noqa: BLE001
                    results.append(
                        {
                            "member": item.get("member", 0) or 0,
                            "status": "error",
                            "error": str(exc),
                        }
                    )

        any_error = any(r.get("status") == "error" for r in results)
        return Response({"results": results}, status=207 if any_error else 201)

    def process_item(self, branch, date, item):
        raise NotImplementedError


class DepositBulkView(_BulkBaseView):
    """Atomic bulk-deposit for Meeting Mode."""

    def process_item(self, branch, date, item):
        member_id = item.get("member")
        amount = int(item.get("amount") or 0)
        if not member_id or amount <= 0:
            return {"member": member_id or 0, "status": "error", "error": "সদস্য ও পরিমাণ দরকার।"}
        member = Member.objects.filter(id=member_id, branch=branch).first()
        if not member:
            return {"member": member_id, "status": "error", "error": "সদস্য পাওয়া যায়নি।"}
        if GeneralJournal.objects.is_already_deposited(date, member, amount):
            return {"member": member_id, "status": "error", "error": "এই পরিমাণ ইতিমধ্যে জমা আছে।"}
        entry = GeneralJournal.objects.deposit_entry(date, member, amount)
        return {"member": member_id, "status": "ok", "id": entry.id}


class InstallmentBulkView(_BulkBaseView):
    """Atomic bulk loan-installment for Meeting Mode."""

    def process_item(self, branch, date, item):
        loan_id = item.get("loan")
        amount = int(item.get("amount") or 0)
        if not loan_id or amount <= 0:
            return {"member": 0, "status": "error", "error": "কর্জ ও পরিমাণ দরকার।"}
        loan = (
            Loan.objects.filter(id=loan_id, branch=branch)
            .select_related("member")
            .first()
        )
        if not loan:
            return {"member": 0, "status": "error", "error": "কর্জ পাওয়া যায়নি।"}
        member_id = loan.member_id
        if loan.is_paid:
            return {"member": member_id, "status": "error", "error": "এই কর্জ ইতিমধ্যে পরিশোধিত।"}
        if amount > loan.total_due:
            return {"member": member_id, "status": "error", "error": f"অতিরিক্ত পরিমাণ — সর্বাধিক {loan.total_due}।"}
        Installment.objects.create(loan=loan, amount=amount, date=date)
        loan.pay_installment(amount)
        GeneralJournal.objects.create_installment_entry(date, loan.member, amount)
        return {"member": member_id, "status": "ok", "id": loan.id}


class FinanceSummaryView(APIView):
    """Today + month income/expense totals for the user's branch."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch = request.user.branch
        today = date_cls.today()
        month_start = today.replace(day=1)

        qs = GeneralTransaction.objects.filter(branch=branch)

        income_today = (
            qs.filter(transaction_type="income", date=today).aggregate(s=Sum("amount"))["s"] or 0
        )
        expense_today = (
            qs.filter(transaction_type="expense", date=today).aggregate(s=Sum("amount"))["s"] or 0
        )
        income_month = (
            qs.filter(transaction_type="income", date__gte=month_start).aggregate(s=Sum("amount"))["s"] or 0
        )
        expense_month = (
            qs.filter(transaction_type="expense", date__gte=month_start).aggregate(s=Sum("amount"))["s"] or 0
        )

        return Response(
            {
                "income_today": income_today,
                "expense_today": expense_today,
                "income_month": income_month,
                "expense_month": expense_month,
            }
        )
