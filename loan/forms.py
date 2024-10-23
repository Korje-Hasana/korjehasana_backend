from django import forms
from .models import LoanReason

class LoadReasonForm(forms.ModelForm):
    class Meta:
        model = LoanReason
        fields = ['reason']

    def __init__(self, *args, **kwargs):
        super(LoadReasonForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})