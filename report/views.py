from django.shortcuts import render
from .services.report_service import ReportService

def report(reqeust):
    report_service = ReportService(branch=reqeust.user.branch)
    months, total_loans, total_installments = report_service.get_monthly_loan_installment_report(branch=reqeust.user.branch)

    # Monthly Collection Percentages report
    monthly_collection_percentages = report_service.get_monthly_collection_percentages()
    collection_months = list(monthly_collection_percentages.keys())
    collection_percentages = list(monthly_collection_percentages.values())
    context = {
        "months": months,
        "total_loans": total_loans,
        "total_installments": total_installments,
        "collection_month": collection_months,
        "collection_percentages": collection_percentages,
    }
    return render(reqeust, 'report.html', context)