from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from peoples.models import Staff

from .models import User, Team, Branch


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}


class UserDetailSerializer(serializers.ModelSerializer):
    """Full user info returned by login + /auth/me/."""

    branch_name = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "role",
            "branch",
            "branch_name",
            "organization_name",
            "is_active",
            "is_staff",
        ]

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else None

    def get_organization_name(self, obj):
        if obj.branch and obj.branch.organization:
            return obj.branch.organization.name
        return None


class UserSerilizerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ["token"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        access = refresh.access_token

        user_data = {
            "username": obj.username,
        }
        access["user"] = user_data

        return {
            "refresh": str(refresh),
            "access": str(access),
        }


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom claims kept in the token (used by web)
        user_data = {
            "username": user.username,
            "branch": user.branch.id if user.branch else None,
            "role": user.role,
        }
        token["user"] = user_data
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Mobile reads branch_name + organization_name from this user object.
        data["user"] = UserDetailSerializer(self.user).data
        return data


class MyRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.verify()
                user = token.payload.get("user")
                # Add custom claims
                user_data = {
                    "username": user.username,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                }
                new_token = RefreshToken.for_user(user)
                new_token["user"] = user_data
                return {"access": str(new_token)}
            except Exception:
                raise serializers.ValidationError("Invalid token")
        else:
            raise serializers.ValidationError("Refresh token is required")


class TeamSerializerBase(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = (
            "id",
            "name",
            "address",
            "member_count",
        )

    def get_member_count(self, obj):
        return obj.members.filter(is_active=True).count()


class TeamSerializer(TeamSerializerBase):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta(TeamSerializerBase.Meta):
        fields = TeamSerializerBase.Meta.fields + ("owner",)

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("দলের নাম দরকার।")
        request = self.context.get("request")
        branch = request.user.branch if request and request.user.is_authenticated else None
        if branch:
            qs = Team.objects.filter(branch=branch, name=value)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    f"এই শাখায় ‘{value}’ নামে একটি দল ইতিমধ্যে আছে।"
                )
        return value


class TeamDetailSerializer(TeamSerializerBase):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(
            {
                "org_name": instance.branch.organization.name,
                "branch_name": instance.branch.name,
                "total_unpaid_loan": instance.total_unpaid_loan(),
                "total_deposit": instance.total_deposit(),
                "active_loan": instance.active_loan(),
            }
        )
        return data


# Staff List Serializer
class StaffListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = "__all__"


# Branch Serializer
class BranchSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source="organization.name")

    class Meta:
        model = Branch
        fields = ("id", "name", "address", "organization")


# Logout Serializer
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
