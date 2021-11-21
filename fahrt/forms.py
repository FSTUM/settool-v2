from datetime import date
from typing import List

from bootstrap_datepicker_plus import DatePickerInput, DateTimePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from settool_common.forms import SemesterBasedForm, SemesterBasedModelForm
from settool_common.models import Subject
from settool_common.utils import produce_field_with_autosubmit

from .models import Fahrt, FahrtMail, Participant, Transportation, TransportationComment


class FahrtForm(forms.ModelForm):
    class Meta:
        model = Fahrt
        exclude: List[str] = ["semester"]
        widgets = {
            "date": DatePickerInput(format="%Y-%m-%d"),
            "open_registration": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
            "close_registration": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
        }


class ParticipantAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Participant
        exclude = ["uuid", "semester", "registration_time", "transportation"]
        widgets = {
            "paid": DatePickerInput(format="%Y-%m-%d"),
            "payment_deadline": DatePickerInput(format="%Y-%m-%d"),
            "non_liability": DatePickerInput(format="%Y-%m-%d"),
        }

    def clean(self):
        cleaned_data = super().clean()
        birthday = cleaned_data["birthday"]
        if birthday == date.today():
            self.add_error("birthday", _("You cant be born today."))
            raise ValidationError(_("You cant be born today."), code="birthday")
            # required, as current template does not have an error place
        if birthday > date.today():
            self.add_error("birthday", _("You cant be born in the future."))
            raise ValidationError(_("You cant be born in the future."), code="birthday")
        return cleaned_data


class ParticipantForm(ParticipantAdminForm):
    class Meta:
        model = Participant
        exclude = [
            "uuid",
            "semester",
            "non_liability",
            "paid",
            "payment_deadline",
            "status",
            "mailinglist",
            "comment",
            "registration_time",
            "transportation",
        ]
        widgets = {
            "birthday": DatePickerInput(format="%Y-%m-%d"),
        }

    car = forms.BooleanField(
        label=_("I habe access to a car and could drive it"),
        required=False,
    )

    car_places = forms.IntegerField(
        label=_("Maximum number of people I could take along additionally"),
        required=False,
        min_value=0,
    )

    dsgvo = forms.BooleanField(
        label=_("I accept the terms and conditions of the following privacy policy:"),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["car"] and not cleaned_data["car_places"]:
            self.add_error("car_places", _("This field is required if you have a car"))

    def save(self, commit=True):
        participant: Participant = super().save(commit=False)

        if self.cleaned_data["car"]:
            car_places: int = self.cleaned_data["car_places"]
            participant.transportation = Transportation.objects.update_or_create(
                transport_type=Transportation.CAR,
                creator=participant,
                fahrt=participant.semester.fahrt,
                places=1 + car_places,
            )
        participant.save()


class AddParticipantToTransportForm(SemesterBasedForm):
    person = forms.ModelChoiceField(
        queryset=None,
        label=_("Unassigned participant"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person"].queryset = self.semester.fahrt_participant.filter(
            transportation=None,
            status="confirmed",
        ).all()


class TransportForm(SemesterBasedModelForm):
    class Meta:
        model = Transportation
        exclude: List[str] = ["fahrt"]
        widgets = {
            "deparure_time": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
            "return_departure_time": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
        }

    def __init__(self, *args, **kwargs):
        self.transport_type = kwargs.pop("transport_type")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not 0 < cleaned_data["places"] < 30:
            self.add_error("places", _("We only allow 0 < places < 30."))
        return cleaned_data

    def save(self, commit=True):
        transport: Transportation = super().save(commit=False)
        transport.fahrt = self.semester.fahrt
        transport.transport_type = self.transport_type
        if commit:
            transport.save()
        return transport


class TransportOptionForm(TransportForm):
    class Meta(TransportForm.Meta):
        exclude: List[str] = ["fahrt", "creator", "transport_type"]

    def __init__(self, *args, **kwargs):
        self.creator = kwargs.pop("creator")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        transport: Transportation = super().save(commit=False)
        transport.creator = self.creator
        transport.save()
        # we cannot respect the commit paramether, because we could need to change the creators transport
        if transport.creator.transportation != transport:
            transport.creator.transportation = transport
            transport.creator.save()
        return transport


class TransportAdminOptionForm(TransportForm):
    class Meta(TransportForm.Meta):
        exclude: List[str] = ["fahrt", "transport_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["creator"].queryset = self.semester.fahrt_participant.filter(transportation=None).all()

    def save(self, commit=True):
        transport: Transportation = super().save(commit=False)
        transport.transport_type = self.transport_type
        transport.save()
        # we cannot respect the commit paramether, because we could need to change the creators transport
        if transport.creator.transportation != transport:
            transport.creator.transportation = transport
            transport.creator.save()
        return transport


class MailForm(forms.ModelForm):
    class Meta:
        model = FahrtMail
        exclude: List[str] = ["sender"]


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=FahrtMail.objects.all(),
        label=_("Email template:"),
    )


def produce_nullboolean_field_with_autosubmit(label):
    return produce_field_with_autosubmit(forms.NullBooleanField, label)


class FilterRegisteredParticipantsForm(SemesterBasedForm):
    non_liability = produce_nullboolean_field_with_autosubmit(_("Non-liability submitted"))
    u18 = produce_nullboolean_field_with_autosubmit(_("Under 18"))
    car = produce_nullboolean_field_with_autosubmit(_("Driver of Car"))
    paid = produce_nullboolean_field_with_autosubmit(_("Paid"))
    payment_deadline = produce_nullboolean_field_with_autosubmit(_("Payment deadline over"))
    mailinglist = produce_nullboolean_field_with_autosubmit(_("On mailinglist"))
    subject = produce_field_with_autosubmit(forms.ModelChoiceField, _("Subject"), queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = self.get_choosable_subjects()

    def get_choosable_subjects(self) -> QuerySet[Subject]:
        choosable_subjects_ids = (
            self.semester.fahrt_participant.filter(status="confirmed")
            .values("subject")
            .distinct()
            .values_list("subject", flat=True)
        )
        return Subject.objects.filter(pk__in=choosable_subjects_ids).order_by("subject")


class FilterParticipantsForm(forms.Form):
    search = forms.CharField(label=_("Search pattern:"), required=False)
    non_liability = forms.NullBooleanField(label=_("Non-liability submitted"))
    u18 = forms.NullBooleanField(label=_("Under 18"))
    car = forms.NullBooleanField(label=_("Driver of car"))
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
    selected = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(attrs={"class": "selectTarget"}),
        required=False,
    )


class SelectParticipantSwitchForm(forms.Form):
    id = forms.IntegerField()
    selected = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(
            attrs={
                "data-toggle": "switchbutton",
                "data-offstyle": "secondary",
                "data-onlabel": _("Is<br>Paid"),
                "data-offlabel": _("NOT<br>Paid"),
            },
        ),
        required=False,
    )


class ParticipantSelectForm(SemesterBasedForm):
    selected = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.widgets.Select(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selected"].queryset = self.semester.fahrt_participant.filter(status="confirmed").all()


class CSVFileUploadForm(forms.Form):
    file = forms.FileField(
        allow_empty_file=False,
        label=_(
            "Upload a csv-file in CSV-CAMT format. "
            "(encoding='iso-8859-1', Semicolon-Seperated, First line is header, Column-order: {fields}) ",
        ).format(
            fields="Auftragskonto;Buchungstag;Valutadatum;Buchungstext;Verwendungszweck;Glaeubiger ID;"
            "Mandatsreferenz;Kundenreferenz (End-to-End);Sammlerreferenz;Lastschrift Ursprungsbetrag;"
            "Auslagenersatz Ruecklastschrift;Beguenstigter/Zahlungspflichtiger;Kontonummer/IBAN;"
            "BIC (SWIFT-Code);Betrag;Waehrung;Info",
        ),
    )


class TransportationCommentForm(forms.ModelForm):
    class Meta:
        model = TransportationComment
        exclude: List[str] = ["sender", "commented_on"]

    def __init__(self, *args, **kwargs):
        self.transport = kwargs.pop("transport")
        self.participant = kwargs.pop("participant")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        t_comment: TransportationComment = super().save(commit=False)
        t_comment.commented_on = self.transport
        t_comment.sender = self.participant
        t_comment.save()
