from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": 'form-control'})
        self.fields["password"].widget.attrs.update({"class": 'form-control'})

class ChangePasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="Password", widget=forms.PasswordInput, required=True)
    new_password2 = forms.CharField(label="Confirm Password",widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update({"class": 'form-control'})
        self.fields["new_password2"].widget.attrs.update({"class": 'form-control'})

    class Meta:
        model = User
        # fields = ['new_password1', 'new_password2']