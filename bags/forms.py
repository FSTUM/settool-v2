from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Company, Mail

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ["semester"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(CompanyForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(CompanyForm, self).save(False)
        instance.semester = self.semester
        if commit:
            instance.save()
        return instance


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude = ["semester"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(MailForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(MailForm, self).save(False)
        instance.semester = self.semester
        if commit:
            instance.save()
        return instance


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=None,
        label=_("Email template:"),
    )

    def __init__(self, *args, **kwargs):
        semester = kwargs.pop('semester')
        super(SelectMailForm, self).__init__(*args, **kwargs)

        self.fields['mail'].queryset = semester.mail_set.all()

class FilterCompaniesForm(forms.Form):
    search = forms.CharField(
        label=_("Search pattern:"),
        required=False,
    )

    no_email_sent = forms.BooleanField(
        label=_("Email was not (successfully) sent"),
        required=False,
    )

    arrived = forms.BooleanField(
        label=_("Giveaways already arrived"),
        required=False,
    )

    last_year = forms.BooleanField(
        label=_("Participated last year"),
        required=False,
    )

    not_last_year = forms.BooleanField(
        label=_("Not participated last year"),
        required=False,
    )

    contact_again = forms.BooleanField(
        label=_("Contact again this year"),
        required=False,
    )

