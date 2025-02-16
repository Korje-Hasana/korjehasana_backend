from django.shortcuts import render
from .services.report_service import ReportService

def report(reqeust):
    report_service = ReportService()
    months, total_loans, total_installments = report_service.get_monthly_loan_installment_report(branch=reqeust.user.branch)
    context = {
        "months": months,
        "total_loans": total_loans,
        "total_installments": total_installments
    }
    return render(reqeust, 'report.html', context)