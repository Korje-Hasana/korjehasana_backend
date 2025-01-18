from django.shortcuts import render

def report(reqeust):
    return render(reqeust, 'report/report.html', context={})