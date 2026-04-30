from rest_framework import serializers
from .models import GeneralTransaction, Loan, Installment, TransactionCategory
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

    def validate(self, attrs):
        loan = attrs.get("loan")
        amount = attrs.get("amount")
        if loan and loan.is_paid:
            raise serializers.ValidationError(
                {"loan": ["এই কর্জ ইতিমধ্যে পরিশোধিত।"]}
            )
        if loan and amount and amount > loan.total_due:
            raise serializers.ValidationError(
                {"amount": [f"অতিরিক্ত পরিমাণ — সর্বাধিক {loan.total_due}।"]}
            )
        return attrs


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Mobile expects `kind` (alias of `category_type`)."""

    kind = serializers.CharField(source="category_type", required=False)

    class Meta:
        model = TransactionCategory
        fields = ("id", "name", "kind")


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
