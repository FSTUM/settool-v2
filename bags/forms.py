from typing import List

from django import forms
from django.utils.translation import ugettext_lazy as _

from settool_common.models import Semester

from .models import BagMail
from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ["semester"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(False)
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
        semester = kwargs.pop("semester")
        super().__init__(*args, **kwargs)

        self.fields["company"].queryset = semester.company_set.filter(
            giveaways="",
        ).order_by("name")


class MailForm(forms.ModelForm):
    class Meta:
        model = BagMail
        exclude: List[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(False)
        if commit:
            instance.save()
        return instance


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=None,
        label=_("Email template:"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mail"].queryset = BagMail.objects.all()


def produce_boolean_field_with_autosubmit(label):
    tmp = forms.BooleanField(
        label_suffix=label,
        required=False,
    )

    tmp.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"
    return tmp


class FilterCompaniesForm(forms.Form):
    no_email_sent = produce_boolean_field_with_autosubmit(_("Email was not (successfully) sent"))
    last_year = produce_boolean_field_with_autosubmit(_("Participated last year"))
    not_last_year = produce_boolean_field_with_autosubmit(_("Not participated last year"))
    contact_again = produce_boolean_field_with_autosubmit(_("Contact again next year"))
    promise = produce_boolean_field_with_autosubmit(_("Promise given"))
    no_promise = produce_boolean_field_with_autosubmit(_("No promise"))
    giveaways = produce_boolean_field_with_autosubmit(_("Giveaways set"))
    arrived = produce_boolean_field_with_autosubmit(_("Giveaways already arrived"))


class SelectCompanyForm(forms.Form):
    id = forms.IntegerField()
    selected = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(attrs={"class": "selectTarget"}),
        required=False,
    )


class ImportForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=None,
        label=_("Import from semester"),
    )

    only_contact_again = forms.BooleanField(
        label=_(
            "Only companies who explicitly said contact again (otherwise all companies except the "
            "ones which said to not contact again will be used)",
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        semester = kwargs.pop("semester")
        super().__init__(*args, **kwargs)

        self.fields["semester"].queryset = Semester.objects.exclude(pk=semester.pk)


class UpdateFieldForm(forms.Form):
    pk = forms.IntegerField()

    name = forms.CharField()

    value = forms.CharField()
