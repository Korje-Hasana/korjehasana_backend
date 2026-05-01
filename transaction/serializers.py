from rest_framework import serializers
from .models import GeneralTransaction, Loan, LoanRequest, Installment, TransactionCategory
from journal.models import GeneralJournal


class DepositSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField()

    class Meta:
        model = GeneralJournal
        fields = ("member", "amount", "date")


class LoanDisbursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ("amount", "date", "member", "total_installment")


class LoanInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = ("amount", "date", "loan")
        # Auto-generated UniqueTogetherValidator returns its message in
        # English; we run our own check in validate() with a Bengali one.
        validators = []

    def validate(self, attrs):
        loan = attrs.get("loan")
        amount = attrs.get("amount")
        date = attrs.get("date")
        if loan and loan.is_paid:
            raise serializers.ValidationError(
                {"loan": ["এই কর্জ ইতিমধ্যে পরিশোধিত।"]}
            )
        if loan and amount and amount > loan.total_due:
            raise serializers.ValidationError(
                {"amount": [f"অতিরিক্ত পরিমাণ — সর্বাধিক {loan.total_due}।"]}
            )
        if loan and date:
            if Installment.objects.filter(loan=loan, date=date).exists():
                raise serializers.ValidationError(
                    {"date": ["এই তারিখে এই কর্জের কিস্তি ইতিমধ্যে জমা আছে।"]}
                )
        return attrs


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Mobile expects `kind` (alias of `category_type`)."""

    kind = serializers.CharField(source="category_type", required=False)

    class Meta:
        model = TransactionCategory
        fields = ("id", "name", "kind")


class LoanRequestSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.name", read_only=True)
    member_serial = serializers.IntegerField(source="member.serial_number", read_only=True)
    team_name = serializers.CharField(source="member.team.name", read_only=True)
    loan_reason_name = serializers.CharField(source="loan_reason.name", read_only=True, default=None)
    has_active_loan = serializers.SerializerMethodField()

    class Meta:
        model = LoanRequest
        fields = (
            "id",
            "member",
            "member_name",
            "member_serial",
            "team_name",
            "requested_amount",
            "total_installment",
            "loan_reason",
            "loan_reason_name",
            "note",
            "position",
            "status",
            "has_active_loan",
            "created_at",
        )
        read_only_fields = ("position", "status", "created_at")

    def get_has_active_loan(self, obj):
        return Loan.objects.filter(member=obj.member, is_paid=False).exists()


class GeneralTransactionSerializer(serializers.ModelSerializer):
    """Income / expense transaction.

    Mobile contract: `{id, kind, category: {...}, amount, date, remark}`.
    Web legacy: still accepts `summary` on write, returns it as `remark`.
    """

    kind = serializers.CharField(source="transaction_type", read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=TransactionCategory.objects.all(), write_only=True
    )
    category_detail = TransactionCategorySerializer(source="category", read_only=True)
    remark = serializers.CharField(
        source="summary", required=False, allow_blank=True, allow_null=True, default=""
    )

    class Meta:
        model = GeneralTransaction
        fields = (
            "id",
            "amount",
            "date",
            "category",
            "category_detail",
            "remark",
            "kind",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Surface category_detail as `category` for the client and drop
        # the write-only id duplicate.
        cat = data.pop("category_detail", None)
        if cat is not None:
            data["category"] = cat
        return data
