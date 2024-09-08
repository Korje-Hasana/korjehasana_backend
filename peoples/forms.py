from django import forms
from .models import Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        exclude = ['created_at', 'updated_at', 'uuid', 'branch', 'is_active', 'team']

    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        # Add 'form-control' class to each field
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
