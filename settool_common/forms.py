from typing import List

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


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude: List[str] = []


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=None,
        label=_("Email template:"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mail"].queryset = Mail.objects.all()


class CSVFileUploadForm(forms.Form):
    file = forms.FileField(
        allow_empty_file=False,
        label=_(
            "Upload a csv-file in exel-formatting. "
            "(Column-order: sender,subject,text,comment. First line is header.)",
        ),
    )
