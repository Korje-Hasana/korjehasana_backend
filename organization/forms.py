from django import forms
from .models import Team, ContactUs
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "address"]


class ContactUsForm(forms.ModelForm):
    recaptcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = ContactUs
        fields = [
            "name",
            "email",
            "subject",
            "message",
            'recaptcha',
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-300",
                    "placeholder": "আপনার নাম",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-300",
                    "placeholder": "আপনার ইমেইল",
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-300",
                    "placeholder": "বার্তার বিষয়",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "cols": 40,
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-300",
                    "placeholder": "আপনার বার্তা লিখুন",
                }
            ),
        }
