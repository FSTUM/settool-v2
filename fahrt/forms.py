from django import forms

from .models import Participant

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
    class Meta:
        model = Participant
        exclude = ["semester", "non_liability", "paid", "payment_deadline",
            "status", "mailinglist", "comment", "registration_time"]
