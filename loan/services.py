from .repositories import LoanRepository


class LoanService:
    """Service for loan business logic"""

    def __init__(self):
        self.repository = LoanRepository()

    def get_user_loans(self, user, search_params=None):
        """Get loans for a specific user's branch with optional filtering"""
        search_params = search_params or {}

        # Get base queryset
        queryset = self.repository.get_base_queryset()

        # Apply branch filtering
        queryset = self.repository.filter_by_branch(queryset, user.branch)

        # Apply unpaid filter
        queryset = self.repository.filter_unpaid(queryset)

        # Apply search and filters
        queryset = self._apply_filters(queryset, search_params)

        return queryset

    def get_admin_loans(self, search_params=None):
        """Get all loans for admin with optional filtering"""
        search_params = search_params or {}

        # Get base queryset (no branch filtering for admin)
        queryset = self.repository.get_base_queryset()

        # Apply branch filter if specified
        branch_id = search_params.get('branch')
        if branch_id:
            queryset = self.repository.filter_by_branch_id(queryset, branch_id)

        # Apply search and filters
        queryset = self._apply_filters(queryset, search_params)

        return queryset

    def _apply_filters(self, queryset, search_params):
        """Apply common filters to queryset"""
        # Search
        if 'q' in search_params:
            queryset = self.repository.search(queryset, search_params['q'])

        # Date range
        queryset = self.repository.filter_by_date_range(
            queryset,
            search_params.get('startdate'),
            search_params.get('enddate')
        )

        # Ordering
        order_by = search_params.get('order_by', 'date')
        direction = search_params.get('direction', 'desc')
        print("order_by:", order_by, "direction:", direction)
        queryset = self.repository.order_queryset(queryset, order_by, direction)

        return queryset

    def calculate_total_loan_amount(self, queryset):
        """Calculate total loan amount for given queryset"""
        return self.repository.calculate_total_amount(queryset)