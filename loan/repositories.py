from django.db.models import Q, Sum
from transaction.models import Loan


class LoanRepository:
    """Repository for loan data access"""

    @staticmethod
    def get_base_queryset():
        return Loan.objects.select_related('member')

    @staticmethod
    def filter_by_branch(queryset, branch):
        return queryset.filter(member__branch=branch)

    @staticmethod
    def filter_by_branch_id(queryset, branch_id):
        if branch_id:
            return queryset.filter(member__branch_id=branch_id)
        return queryset

    @staticmethod
    def filter_unpaid(queryset):
        return queryset.filter(is_paid=False)

    @staticmethod
    def search(queryset, query):
        if not query:
            return queryset
        return queryset.filter(
            Q(member__name__icontains=query) |
            Q(amount__icontains=query) |
            Q(date__icontains=query)
        )

    @staticmethod
    def filter_by_date_range(queryset, start_date=None, end_date=None):
        if start_date and end_date:
            return queryset.filter(date__range=[start_date, end_date])
        elif start_date:
            return queryset.filter(date__gte=start_date)
        elif end_date:
            return queryset.filter(date__lte=end_date)
        return queryset

    @staticmethod
    def order_queryset(queryset, order_by='date', direction='desc'):
        if direction == 'desc' and not order_by.startswith('-'):
            order_by = f'-{order_by}'

        print("---- Order By:", order_by)
        return queryset.order_by(order_by)

    @staticmethod
    def calculate_total_amount(queryset):
        return queryset.aggregate(total=Sum('amount'))['total'] or 0