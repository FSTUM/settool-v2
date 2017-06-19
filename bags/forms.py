from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Company, Mail
from settool_common.models import Semester

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


class GiveawayForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=None,
        label=_("Company"),
    )

    giveaways = forms.CharField(
        label=_("Giveaways"),
    )

    def __init__(self, *args, **kwargs):
        semester = kwargs.pop('semester')
        super(GiveawayForm, self).__init__(*args, **kwargs)

        self.fields['company'].queryset = semester.company_set.filter(
            giveaways="").order_by('name')


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
    search.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    no_email_sent = forms.BooleanField(
        label=_("Email was not (successfully) sent"),
        required=False,
    )
    no_email_sent.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    last_year = forms.BooleanField(
        label=_("Participated last year"),
        required=False,
    )
    last_year.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    not_last_year = forms.BooleanField(
        label=_("Not participated last year"),
        required=False,
    )
    not_last_year.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    contact_again = forms.BooleanField(
        label=_("Contact again next year"),
        required=False,
    )
    contact_again.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    promise = forms.BooleanField(
        label=_("Promise given"),
        required=False,
    )
    promise.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    no_promise = forms.BooleanField(
        label=_("No promise"),
        required=False,
    )
    no_promise.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    giveaways = forms.BooleanField(
        label=_("Giveaways set"),
        required=False,
    )
    giveaways.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    arrived = forms.BooleanField(
        label=_("Giveaways already arrived"),
        required=False,
    )
    arrived.widget.attrs["onchange"]="document.getElementById('filterform').submit()"


class SelectCompanyForm(forms.Form):
    id = forms.IntegerField()

    selected = forms.BooleanField(
        required=False,
    )


class ImportForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=None,
        label=_("Import from semester"),
    )

    only_contact_again = forms.BooleanField(
        label=_("Only companies who explicitly said contact again (otherwise \
            all companies except the ones which said to not contact again \
            will be used)"),
        required=False,
    )   

    def __init__(self, *args, **kwargs):
        semester = kwargs.pop('semester')
        super(ImportForm, self).__init__(*args, **kwargs)

        self.fields['semester'].queryset = Semester.objects.exclude(pk=semester.pk)
