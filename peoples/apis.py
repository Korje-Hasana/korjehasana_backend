from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from transaction.models import Loan, Savings

from peoples.models import Member
from peoples.permissions import IsSameBranch
from peoples.serializers import (
    MemberCreateSerializer,
    MemberDetailSerializer,
    MemberSavingsLoanInfoSerializer,
)


class MemberListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["team", "is_active", "gender"]
    search_fields = ["name", "guardian_name", "mobile_number"]
    pagination_class = None  # mobile expects flat list

    def get_queryset(self):
        qs = Member.active_objects.filter(branch=self.request.user.branch).select_related(
            "team", "branch"
        )
        params = self.request.query_params

        # Free-text search across name / guardian / mobile
        q = params.get("q")
        if q:
            q = q.strip()
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(guardian_name__icontains=q)
                | Q(mobile_number__icontains=q)
            )

        # Filter to members with an active (unpaid) loan
        has_loan = params.get("has_active_loan")
        if has_loan in {"true", "1", "True"}:
            qs = qs.filter(loan__is_paid=False).distinct()
        elif has_loan in {"false", "0", "False"}:
            qs = qs.exclude(loan__is_paid=False).distinct()

        return qs.order_by("team__name", "serial_number")

    def perform_create(self, serializer):
        serializer.save(branch=self.request.user.branch)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MemberCreateSerializer
        return MemberDetailSerializer


class MemberDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSameBranch]
    serializer_class = MemberDetailSerializer

    def get_object(self):
        member = get_object_or_404(Member, id=self.kwargs.get("id"))
        # Defence-in-depth: ensure same-branch (also enforced by permission).
        if member.branch_id != self.request.user.branch_id:
            self.permission_denied(self.request)
        return member


class MemberSavingLoanInfo(APIView):
    serializer_class = MemberSavingsLoanInfoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        member = get_object_or_404(Member, id=kwargs.get("id"))
        savings = (
            Savings.objects.filter(member=member).aggregate(Sum("amount"))["amount__sum"]
        )
        last_loan = Loan.objects.filter(member=member).last()
        total_loan = Loan.objects.filter(member=member).count()

        data = {
            "total_savings": savings if savings else 0,
            "last_loan": last_loan.amount if last_loan else 0,
            "loan_date": last_loan.date if last_loan else None,
            "loan_paid": last_loan.total_paid if last_loan else 0,
            "installment_paid": last_loan.installment_paid if last_loan else 0,
            "total_loan_count": total_loan,
        }
        serializer = self.serializer_class(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
