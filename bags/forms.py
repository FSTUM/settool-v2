from bootstrap_modal_forms.forms import BSModalModelForm
from django import forms
from django.utils.translation import gettext as _

from settool_common.forms import produce_csv_file_upload_field, SemesterBasedForm, SemesterBasedModelForm
from settool_common.models import Semester
from settool_common.utils import produce_field_with_autosubmit

from .models import BagMail, BagSettings, Company, Giveaway, GiveawayGroup


class CompanyForm(SemesterBasedModelForm):
    class Meta:
        model = Company
        exclude = ["semester"]


class GiveawayEditForm(SemesterBasedForm, forms.ModelForm):
    class Meta:
        model = Giveaway
        exclude: list[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = self.semester.company_set.all()
        self.fields["group"].queryset = self.semester.giveawaygroup_set.all()


class GiveawayForm(forms.ModelForm):
    group_input = forms.CharField(
        label=_("Giveaway-title/group/tag"),
        widget=forms.TextInput(attrs={"list": "groupDatalist"}),
    )

    class Meta:
        model = Giveaway
        exclude: list[str] = ["group"]
        fields = ["company", "group_input", "comment", "item_count", "arrival_time", "arrived"]

    def clean(self):
        cleaned_data = super().clean()  # pylint: disable=attribute-defined-outside-init
        if self.data is not None and "group_input" in self.data and self.data["group_input"]:
            self.group = GiveawayGroup.objects.get_or_create(semester=self.semester, name=self.data["group_input"])[0]
        return cleaned_data  # noqa: R504

    def __init__(self, *args, **kwargs):
        self.semester: Semester = kwargs.pop("semester")
        self.group = None
        super().__init__(*args, **kwargs)
        if "company" in self.fields:
            self.fields["company"].queryset = self.semester.company_set.all()

    def save(self, commit=True):
        giveaway: Giveaway = super().save(commit=False)
        giveaway.group = self.group
        if commit:
            giveaway.save()
        return giveaway


class GiveawayForCompanyForm(GiveawayForm):
    class Meta:
        model = Giveaway
        exclude = ["company", "group"]
        fields = ["group_input", "comment", "item_count", "arrival_time", "arrived"]

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        giveaway: Giveaway = super().save(commit=False)
        giveaway.company = self.company
        giveaway.save()
        return giveaway


class GiveawayDistributionModelForm(BSModalModelForm):
    class Meta:
        model = Giveaway
        fields = ["item_count", "arrival_time", "comment"]


class GiveawayGroupForm(SemesterBasedModelForm):
    class Meta:
        model = GiveawayGroup
        exclude: list[str] = ["semester"]


class GiveawayToGiveawayGroupForm(SemesterBasedForm):
    giveaway = forms.ModelChoiceField(
        queryset=None,
        label=_("Giveaway"),
    )

    def __init__(self, *args, **kwargs):
        giveaway_group: GiveawayGroup = kwargs.pop("giveaway_group")
        super().__init__(*args, **kwargs)
        self.fields["giveaway"].queryset = Giveaway.objects.exclude(id__in=giveaway_group.giveaway_set.all())


class MailForm(forms.ModelForm):
    class Meta:
        model = BagMail
        exclude: list[str] = ["sender"]


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
    no_giveaway = produce_boolean_field_with_autosubmit(_("No Giveaway exists"))
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


class SelectGiveawaySwitchForm(forms.Form):
    id = forms.IntegerField()
    selected = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(
            attrs={
                "data-toggle": "switchbutton",
                "data-offstyle": "secondary",
                "data-onlabel": _("Has<br>Arrived"),
                "data-offlabel": _("NOT<br>Arrived"),
            },
        ),
        required=False,
    )


class BagSettingsForm(forms.ModelForm):
    class Meta:
        model = BagSettings
        exclude: list[str] = ["semester"]
