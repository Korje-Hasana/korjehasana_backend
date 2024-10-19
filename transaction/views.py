from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from journal.models import GeneralJournal
from organization.models import Branch, Team
from peoples.models import Member
from transaction.forms import InstallmentForm
from transaction.utils import format_savings_date, format_loan_data
from .forms import DepositForm, MemberChoiceForm, LoanDisbursementForm, WithdrawForm


from .models import Loan


@login_required
def dashboard(request):
    branch = request.user.branch
    branch_journal = GeneralJournal.objects.filter(branch=branch)
    balance = branch_journal.filter(accounts__code='CA') \
        .aggregate(balance=Sum('debit') - Sum('credit'))['balance']

    total_deposit = branch_journal.filter(accounts__code='DE').aggregate(deposit=Sum('credit'))['deposit']
    total_withdraw = branch_journal.filter(accounts__code='WI').aggregate(withdraw=Sum('debit'))['withdraw']
    if not total_deposit: total_deposit = 0
    if not total_withdraw: total_withdraw = 0

    total_loan = branch_journal.filter(accounts__code='LO').aggregate(loan=Sum('debit'))['loan']
    total_installment = branch_journal.filter(accounts__code='IN').aggregate(loan=Sum('credit'))['loan']
    if not total_loan: total_loan = 0
    if not total_installment: total_installment = 0

    # Sum of members current balance

    context = {
        "deposit_balance": total_deposit - total_withdraw,  # সঞ্চয় স্থিতি
        "loan_balance": total_loan - total_installment,
        "total_expense": "total_expense",
        "total_income": "total_income",
        "balance": balance,
        "branch": branch
    }
    return render(request, 'transaction/dashboard.html', context)


@login_required
def deposit_list(request, team_id):
    now = datetime.now()
    month = request.GET.get('month', now.month)

    data = []
    members = Member.active_objects.filter(team__id=team_id).order_by("serial_number")
    members = members.filter(team=team_id)

    for member in members:
        savings_data = format_savings_date(member, month)
        data.append(savings_data)
    context = {
        'journals': data,
        'team_id': team_id,
        'month': month
    }

    return render(request, 'transaction/deposit_list.html', context)


@login_required
def loan_list(request, team_id=None):
    data = []
    month = datetime.now().month
    staff_branch = request.user.branch
    active_loans = Loan.objects.filter(
        branch=staff_branch, is_paid=False
    ).select_related("member").order_by("member__serial_number")

    if team_id:
        team = Team.objects.get(id=team_id)
        active_loans = active_loans.filter(team=team)
    for loan in active_loans:
        installment_data = format_loan_data(loan, month)
        data.append(installment_data)

    context = {
        'journals': data,
        'team': team or None
    }

    return render(request, 'transaction/loan_list.html', context)


class DepositPostingView(LoginRequiredMixin, View):
    template_name = 'transaction/deposit_posting.html'

    def get(self, request, *args, **kwargs):
        team_id = request.GET.get('team', None)
        serial_number = request.GET.get('serial_number', 1)
        member = self.get_member(team_id, serial_number)

        form = MemberChoiceForm(initial={'team': team_id, 'serial_number': serial_number}, user=request.user)
        deposit_form = DepositForm()

        context = {
            "member_choice_form": form,
            "deposit_form": deposit_form,
            "member": member,
            "team_id": team_id,
            "serial_number": serial_number,
            "next_sl": int(serial_number) + 1
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        team_id = request.GET.get('team', None)
        serial_number = request.GET.get('serial_number', 1)
        member = self.get_member(team_id, serial_number)

        deposit_form = DepositForm(request.POST)
        if deposit_form.is_valid():
            date = deposit_form.cleaned_data['date']
            amount = deposit_form.cleaned_data['amount']
            try:
                GeneralJournal.objects.deposit_entry(date, member, amount)
                messages.success(request, f'{member.name} {amount} টাকা জমা হয়েছে')
                return HttpResponseRedirect(reverse('deposit_posting') + f'?team={team_id}&serial_number={serial_number}')
            except IntegrityError:
                messages.error(request, f'দুঃখিত, {member.name} ৳{amount} ইতোমধ্যে জমা হয়েছে')

        # If form is not valid or if there's an error, re-render the form with the current context
        form = MemberChoiceForm(initial={'team': team_id, 'serial_number': serial_number}, user=request.user)
        context = {
            "member_choice_form": form,
            "deposit_form": deposit_form,
            "member": member,
            "team_id": team_id,
            "next_sl": int(serial_number) + 1
        }
        return render(request, self.template_name, context)

    def get_member(self, team_id, serial_number):
        if team_id and serial_number:
            try:
                return Member.active_objects.get(team=team_id, serial_number=serial_number)
            except Member.DoesNotExist:
                messages.error(self.request, f'দুঃখিত, এই সিরিয়ালে কোন সদস্য নেই')
        return None


@login_required
def installment_posting(request):
    member = None
    loan = None
    team_id = request.GET.get('team', None)
    serial_number = request.GET.get('serial_number', 1)
    if team_id and serial_number:
        try:
            member = Member.active_objects.get(team=team_id, serial_number=serial_number)
            loan = member.get_my_loan()
        except:
            messages.error(request, f'দুঃখিত, এই সিরিয়ালে কোন সদস্য নেই')

    if request.method == 'POST':
        installment_form = InstallmentForm(request.POST)
        if installment_form.is_valid():
            date = installment_form.cleaned_data['date']
            amount = installment_form.cleaned_data['amount']
            try:
                loan = member.get_my_loan()
                loan.pay_installment(amount)
                GeneralJournal.objects.create_installment_entry(date, member, amount)
                messages.success(request, f'{member.name} {amount} টাকা কর্জ ফেরত জমা হয়েছে')
                if loan.is_paid:
                    messages.success(request, f'{member.name} কর্জ পরিশোধ হয়েছে')
            except IntegrityError as e:
                messages.error(request, f'দুঃখিত, {member.name} ৳{amount} ইতোমধ্যে জমা হয়েছে')

    form = MemberChoiceForm({'team': team_id, 'serial_number': serial_number}, user=request.user)
    installment_form = InstallmentForm()
    context = {
        "member_choice_form": form,
        "installment_form": installment_form,
        "member": member,
        "team_id": team_id,
        "my_loan": loan,
        "next_sl": int(serial_number) + 1
    }
    return render(request, 'transaction/installment_posting.html', context)


class LoanDisbursementView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanDisbursementForm
    template_name = 'transaction/loan_disbursement_form.html'
    success_url = reverse_lazy('loan_list')  # Change to the appropriate URL

    def get_success_url(self):
        return reverse_lazy('loan_list', kwargs={'team_id': self.get_member().team_id})

    def get_member(self):
        member_id = self.kwargs.get('member')
        # Fetch and return the Member object, or raise a 404 error if not found
        return get_object_or_404(Member, id=member_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        return context

    def form_valid(self, form):
        date = form.cleaned_data["date"]
        amount = form.cleaned_data["amount"]
        member = self.get_member()

        if member.has_active_loan():
            messages.error(self.request, 'একটি অপরিশোধিত কর্জ আছে')
            return super().form_invalid(form)

        loan = form.save(commit=False)
        loan.total_due = loan.amount  # Set total due to the amount
        loan.member = member
        loan.branch = member.branch
        loan.team = member.team
        loan.save()

        GeneralJournal.objects.create_loan_entry(date, member, amount)
        messages.success(self.request, f'Loan of {loan.amount} has been successfully disbursed to {loan.member.name}.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error in the form. Please correct the issues below.')
        return super().form_invalid(form)


class WithdrawalPostingView(LoginRequiredMixin, View):
    template_name = 'transaction/withdrawal_posting.html'

    def get(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)
        withdraw_form = WithdrawForm()

        context = {
            "withdraw_form": withdraw_form,
            "member": member,
        }

        return render(request, self.template_name, context)

    def post(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)

        withdraw_form = WithdrawForm(request.POST)
        if withdraw_form.is_valid():
            date = withdraw_form.cleaned_data['date']
            amount = withdraw_form.cleaned_data['amount']
            try:
                GeneralJournal.objects.create_withdraw_entry(date, member, amount)
                messages.success(request, f'{member.name} {amount} টাকা উত্তোলন করা হয়েছে')
                return HttpResponseRedirect(reverse('withdrawal_posting', kwargs={'member_id':member_id}))
            except (IntegrityError, ValidationError) as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(reverse('withdrawal_posting', kwargs={'member_id': member_id}))


    def get_member(self, team_id, serial_number):
        if team_id and serial_number:
            try:
                return Member.active_objects.get(team=team_id, serial_number=serial_number)
            except Member.DoesNotExist:
                messages.error(self.request, f'দুঃখিত, এই সিরিয়ালে কোন সদস্য নেই')
        return None
