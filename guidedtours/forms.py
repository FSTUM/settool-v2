from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Participant, Tour, Mail


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        exclude = ["time"]

    def __init__(self, *args, **kwargs):
        tours = kwargs.pop('tours')
        super(ParticipantForm, self).__init__(*args, **kwargs)
        self.fields['tour'].queryset = tours


class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        exclude = ["semester"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(TourForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TourForm, self).save(False)
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

        self.fields['mail'].queryset = semester.tours_mail_set.all()


class FilterParticipantsForm(forms.Form):
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
        semester = kwargs.pop('semester')
        super(FilterParticipantsForm, self).__init__(*args, **kwargs)

        self.fields['tour'].queryset = semester.tour_set


class SelectParticipantForm(forms.Form):
    id = forms.IntegerField()

    selected = forms.BooleanField(
        required=False,
    )
