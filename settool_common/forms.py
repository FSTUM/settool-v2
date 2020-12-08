from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Mail


class SemesterBasedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super().__init__(*args, **kwargs)


class SemesterBasedModelForm(SemesterBasedForm, forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(False)
        instance.semester = self.semester

        if commit:
            instance.save()

        return instance


class MailForm(SemesterBasedModelForm):
    class Meta:
        model = Mail
        exclude = ["semester"]


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=None,
        label=_("Email template:"),
    )

    def __init__(self, *args, **kwargs):
        semester = kwargs.pop("semester")
        super().__init__(*args, **kwargs)

        self.fields["mail"].queryset = semester.fahrt_mail_set.all()
