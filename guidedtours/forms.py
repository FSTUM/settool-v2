from typing import List

from bootstrap_datepicker_plus import DateTimePickerInput
from django import forms
from django.utils.translation import gettext as _

from settool_common.forms import CommonParticipantForm, SemesterBasedForm, SemesterBasedModelForm

from .models import Participant, Setting, Tour, TourMail


class ParticipantForm(CommonParticipantForm):
    class Meta:
        model = Participant
        exclude = ["time"]

    def __init__(self, *args, **kwargs):
        tours = kwargs.pop("tours")
        super().__init__(*args, **kwargs)
        self.fields["tour"].queryset = tours
        self.fields["tour"].widget.attrs = {"class": "no-automatic-choicejs"}


class TourForm(SemesterBasedModelForm):
    class Meta:
        model = Tour
        exclude = ["semester"]
        widgets = {
            "date": DateTimePickerInput(format="%Y-%m-%d"),
            "open_registration": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
            "close_registration": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
        }


class MailForm(forms.ModelForm):
    class Meta:
        model = TourMail
        exclude: List[str] = ["sender"]


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=TourMail.objects.all(),
        label=_("Email template:"),
    )


class FilterParticipantsForm(SemesterBasedForm):
    search = forms.CharField(
        label=_("Search pattern"),
        required=False,
    )

    on_the_tour = forms.ChoiceField(
        label=_("Status"),
        choices=(
            (None, "-------"),
            (True, _("on the tour")),
            (False, _("on the waitinglist")),
        ),
        required=False,
    )

    tour = forms.ModelChoiceField(
        queryset=None,
        label=_("Tour"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tour"].queryset = self.semester.tour_set


class SelectParticipantForm(forms.Form):
    id = forms.IntegerField()
    selected = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(attrs={"class": "selectTarget"}),
        required=False,
    )


class SettingsAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Setting
        exclude = ["semester"]
