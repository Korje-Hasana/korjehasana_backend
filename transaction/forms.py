from django import forms

from journal.models import Ledger, GeneralJournal
from organization.models import Team
from peoples.models import Member
from .models import Loan


class MemberChoiceForm(forms.Form):
    team = forms.ModelChoiceField(queryset=Team.objects.all())
    serial_number = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Extract the user from the kwargs
        super(MemberChoiceForm, self).__init__(*args, **kwargs)

        # Filter the queryset of the project field based on the user
        self.fields['team'].queryset = Team.objects.filter(owner=user)


class DepositForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}))
    amount = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))


class InstallmentForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}))
    amount = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))


class WithdrawForm(DepositForm):
    pass


class LoanDisbursementForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['date', 'amount', 'total_installment', 'loan_reason']

        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'total_installment': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'loan_reason': forms.Select(attrs={'class': 'form-control'}),
        }

        # add labels for all fields
        labels = {
            'date': 'তারিখ',
            'amount': 'পরিমাণ',
            'total_installment': 'মোট কিস্তি',
            'loan_reason': 'কর্জের কারণ'
        }


    def __init__(self, *args, **kwargs):
        super(LoanDisbursementForm, self).__init__(*args, **kwargs)
        self.fields['total_installment'].initial = 24

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        total_installment = cleaned_data.get('total_installment')
        total_installment = cleaned_data.get('total_installment')

        if amount <= 0:
            self.add_error('amount', "Loan amount must be positive.")

        if total_installment <= 0:
            self.add_error('total_installment', "Total installments must be a positive number.")

        return cleaned_data


class IncomeTransactionForm(forms.ModelForm):
    income_type = forms.ModelChoiceField(queryset=Ledger.objects.filter(ledger_type__code='OI'), widget=forms.Select(attrs={'class': 'form-control'}), label='আয়ের খাত')
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}))
    amount = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = GeneralJournal  # Link this form to GeneralJournal model
        fields = ['income_type', 'date', 'amount']


class ExpenseTransactionForm(forms.ModelForm):
    expense_type = forms.ModelChoiceField(queryset=Ledger.objects.filter(ledger_type__code='OE'), widget=forms.Select(attrs={'class': 'form-control'}), label='ব্যয়ের খাত')
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}))
    amount = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = GeneralJournal  # Link this form to GeneralJournal model
        fields = ['expense_type', 'date', 'amount']
