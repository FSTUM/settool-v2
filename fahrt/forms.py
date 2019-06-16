from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Participant, Mail, Fahrt


class FahrtForm(forms.ModelForm):
    class Meta:
        model = Fahrt
        exclude = ["semester"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(FahrtForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(FahrtForm, self).save(False)
        instance.semester = self.semester
        if commit:
            instance.save()
        return instance


class ParticipantAdminForm(forms.ModelForm):
    class Meta:
        model = Participant
        exclude = ["semester", "registration_time"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(ParticipantAdminForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(ParticipantAdminForm, self).save(False)

        instance.semester = self.semester

        if commit:
            instance.save()

        return instance


class ParticipantForm(ParticipantAdminForm):
    dsgvo = forms.BooleanField(required=True, label=_("I accept the terms and conditions of the following privacy "
                                                      "policy:"))

    class Meta:
        model = Participant
        exclude = ["semester", "non_liability", "paid", "payment_deadline",
                   "status", "mailinglist", "comment", "registration_time"]

    def clean(self):
        cleaned_data = super(ParticipantForm, self).clean()

        if cleaned_data['car'] and not cleaned_data['car_places']:
            self.add_error("car_places",
                           _("This field is required if you have a car"))


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

        self.fields['mail'].queryset = semester.fahrt_mail_set.all()


class FilterParticipantsForm(forms.Form):
    search = forms.CharField(
        label=_("Search pattern:"),
        required=False,
    )

    non_liability = forms.NullBooleanField(
        label=_("Non-liability submitted"),
    )

    u18 = forms.NullBooleanField(
        label=_("Under 18"),
    )

    car = forms.NullBooleanField(
        label=_("With car"),
    )

    paid = forms.NullBooleanField(
        label=_("Paid"),
    )

    payment_deadline = forms.NullBooleanField(
        label=_("Payment deadline over"),
    )

    mailinglist = forms.NullBooleanField(
        label=_("On mailinglist"),
    )

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
        required=False,
    )
