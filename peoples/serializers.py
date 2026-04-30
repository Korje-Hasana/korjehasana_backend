from rest_framework import serializers

from peoples.models import Member
from transaction.models import Loan


class MemberDetailSerializer(serializers.ModelSerializer):
    """Used for list + retrieve. Mobile contract: team {id,name}, includes
    savings_balance and active_loan."""

    team = serializers.SerializerMethodField()
    savings_balance = serializers.SerializerMethodField()
    active_loan = serializers.SerializerMethodField()
    mobile = serializers.CharField(source="mobile_number", read_only=True)

    class Meta:
        model = Member
        fields = (
            "id",
            "serial_number",
            "name",
            "guardian_name",
            "mobile",
            "team",
            "savings_balance",
            "active_loan",
        )

    def get_team(self, obj):
        if not obj.team:
            return None
        return {"id": obj.team.id, "name": obj.team.name}

    def get_savings_balance(self, obj):
        return obj.balance() or 0

    def get_active_loan(self, obj):
        loan = (
            Loan.objects.filter(member=obj, is_paid=False)
            .order_by("-id")
            .first()
        )
        if not loan:
            return None
        monthly = (
            int(loan.amount / loan.total_installment) if loan.total_installment else 0
        )
        return {
            "id": loan.id,
            "amount": loan.amount,
            "total_due": loan.total_due,
            "total_installment": loan.total_installment,
            "installment_paid": loan.installment_paid,
            "monthly_installment": monthly,
        }


class MemberCreateSerializer(serializers.ModelSerializer):
    # Accept either "mobile" (mobile app) or "mobile_number" (legacy web).
    mobile = serializers.CharField(
        source="mobile_number", required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Member
        fields = [
            "id",
            "name",
            "mobile",
            "nid_number",
            "guardian_name",
            "gender",
            "serial_number",
            "team",
        ]
        read_only_fields = ["id"]
        # Drop DRF's auto-generated UniqueTogetherValidator (its message is
        # English and only kicks in when all 3 fields, including is_active,
        # are present in the serializer). We do the duplicate check in
        # validate() with a Bengali message instead.
        validators = []
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "required": "সদস্যের নাম দরকার।",
                    "blank": "সদস্যের নাম দরকার।",
                }
            },
            "team": {
                "error_messages": {
                    "required": "দল নির্বাচন করুন।",
                    "does_not_exist": "দল পাওয়া যায়নি।",
                    "incorrect_type": "দলের আইডি দিন।",
                }
            },
            "serial_number": {
                "error_messages": {
                    "required": "সিরিয়াল নম্বর দরকার।",
                    "invalid": "সিরিয়াল নম্বর সংখ্যা হতে হবে।",
                }
            },
        }

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("সদস্যের নাম দরকার।")
        return value.strip()

    def validate_serial_number(self, value):
        if value < 1:
            raise serializers.ValidationError("সিরিয়াল নম্বর ১ থেকে শুরু হবে।")
        if value > 25:
            raise serializers.ValidationError("সিরিয়াল নম্বর সর্বোচ্চ ২৫ পর্যন্ত হতে পারে।")
        return value

    def validate(self, attrs):
        team = attrs.get("team")
        serial = attrs.get("serial_number")
        if team is not None and serial is not None:
            existing = Member.objects.filter(
                team=team, serial_number=serial, is_active=True
            )
            if self.instance is not None:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {
                        "serial_number": [
                            f"{team.name} দলে এই সিরিয়াল ({serial}) ইতিমধ্যে ব্যবহৃত হয়েছে।"
                        ]
                    }
                )
        return attrs


class MemberSavingsLoanInfoSerializer(serializers.Serializer):
    total_savings = serializers.IntegerField()
    last_loan = serializers.IntegerField()
    loan_date = serializers.DateField()
    loan_paid = serializers.IntegerField()
    installment_paid = serializers.IntegerField()
    total_loan_count = serializers.IntegerField()
