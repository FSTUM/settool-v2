from datetime import date
from typing import List

from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from settool_common.forms import CommonParticipantForm, SemesterBasedModelForm
from settool_common.utils import produce_field_with_autosubmit

from .models import Fahrt, FahrtMail, Participant


class FahrtForm(forms.ModelForm):
    class Meta:
        model = Fahrt
        exclude: List[str] = []
        widgets = {
            "date": DatePickerInput(format="%Y-%m-%d"),
            "open_registration": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
            "close_registration": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
        }


class ParticipantAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Participant
        exclude = ["semester", "registration_time"]


class ParticipantForm(CommonParticipantForm):
    class Meta:
        model = Participant
        exclude = [
            "semester",
            "non_liability",
            "paid",
            "payment_deadline",
            "status",
            "mailinglist",
            "comment",
            "registration_time",
        ]
        widgets = {
            "birthday": DatePickerInput(format="%Y-%m-%d"),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["car"] and not cleaned_data["car_places"]:
            self.add_error("car_places", _("This field is required if you have a car"))
        birthday = cleaned_data["birthday"]
        if birthday == date.today():
            self.add_error("birthday", _("You cant be born today."))
            raise ValidationError(_("You cant be born today."), code="birthday")
            # required, as current template does not have an error place
        if birthday > date.today():
            self.add_error("birthday", _("You cant be born in the future."))
            raise ValidationError(_("You cant be born in the future."), code="birthday")


class MailForm(forms.ModelForm):
    class Meta:
        model = FahrtMail
        exclude: List[str] = []


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=FahrtMail.objects.all(),
        label=_("Email template:"),
    )


def produce_nullboolean_field_with_autosubmit(label):
    return produce_field_with_autosubmit(forms.NullBooleanField, label)


class FilterRegisteredParticipantsForm(forms.Form):
    non_liability = produce_nullboolean_field_with_autosubmit(_("Non-liability submitted"))
    u18 = produce_nullboolean_field_with_autosubmit(_("Under 18"))
    car = produce_nullboolean_field_with_autosubmit(_("With car"))
    paid = produce_nullboolean_field_with_autosubmit(_("Paid"))
    payment_deadline = produce_nullboolean_field_with_autosubmit(_("Payment deadline over"))
    mailinglist = produce_nullboolean_field_with_autosubmit(_("On mailinglist"))


class FilterParticipantsForm(forms.Form):
    search = forms.CharField(label=_("Search pattern:"), required=False)
    non_liability = forms.NullBooleanField(label=_("Non-liability submitted"))
    u18 = forms.NullBooleanField(label=_("Under 18"))
    car = forms.NullBooleanField(label=_("With car"))
    paid = forms.NullBooleanField(label=_("Paid"))
    payment_deadline = forms.NullBooleanField(label=_("Payment deadline over"))
    mailinglist = forms.NullBooleanField(label=_("On mailinglist"))

    status = forms.ChoiceField(
        label=_("Status"),
        choices=(
            ("", "-------"),
            ("registered", _("registered")),
            ("confirmed", _("confirmed")),
            ("waitinglist", _("waitinglist")),
            ("cancelled", _("cancelled")),
        ),
        required=False,
    )


class SelectParticipantForm(forms.Form):
    id = forms.IntegerField()

    selected = forms.BooleanField(required=False)
