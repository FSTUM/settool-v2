from typing import List

from django import forms
from django.utils.translation import ugettext_lazy as _

from settool_common.forms import produce_csv_file_upload_field, SemesterBasedForm, SemesterBasedModelForm
from settool_common.models import Semester
from settool_common.utils import produce_field_with_autosubmit

from .models import BagMail, Company, Giveaway, GiveawayGroup


class CompanyForm(SemesterBasedModelForm):
    class Meta:
        model = Company
        exclude = ["semester"]


class GiveawayForm(SemesterBasedModelForm):
    class Meta:
        model = Giveaway
        exclude: List[str] = []


class GiveawayGroupForm(SemesterBasedModelForm):
    class Meta:
        model = GiveawayGroup
        exclude: List[str] = ["semester"]


class MailForm(forms.ModelForm):
    class Meta:
        model = BagMail
        exclude: List[str] = ["sender"]


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=BagMail.objects.all(),
        label=_("Email template:"),
    )


def produce_boolean_field_with_autosubmit(label):
    return produce_field_with_autosubmit(forms.BooleanField, label)


class FilterCompaniesForm(forms.Form):
    no_email_sent = produce_boolean_field_with_autosubmit(_("Email was not (successfully) sent"))
    last_year = produce_boolean_field_with_autosubmit(_("Participated last year"))
    not_last_year = produce_boolean_field_with_autosubmit(_("Not participated last year"))
    contact_again = produce_boolean_field_with_autosubmit(_("Contact again next year"))
    promise = produce_boolean_field_with_autosubmit(_("Promise given"))
    no_promise = produce_boolean_field_with_autosubmit(_("No promise"))
    giveaways = produce_boolean_field_with_autosubmit(_("At least one Giveaway exists"))
    arrived = produce_boolean_field_with_autosubmit(_("Giveaways already arrived"))


class SelectCompanyForm(forms.Form):
    id = forms.IntegerField()
    selected = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(attrs={"class": "selectTarget"}),
        required=False,
    )


class ImportForm(SemesterBasedForm):
    old_semester = forms.ModelChoiceField(
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
        super().__init__(*args, **kwargs)
        self.fields["old_semester"].queryset = Semester.objects.exclude(pk=self.semester.pk)


class UpdateFieldForm(forms.Form):
    pk = forms.IntegerField()
    name = forms.CharField()
    value = forms.CharField()


class CSVFileUploadForm(forms.Form):
    file = produce_csv_file_upload_field(
        "name, contact_gender, contact_firstname, contact_lastname, email, "
        "email_sent, email_sent_success, promise, giveaways, giveaways_last_year, "
        "arrival_time, comment, last_year, arrived, contact_again",
    )
