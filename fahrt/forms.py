from django import forms

from .models import Participant

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        exclude = ["semester", "non_liability", "paid", "payment_deadline",
            "status", "mailinglist", "comment", "registration_time"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(ParticipantForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(ParticipantForm, self).save(False)

        instance.semester = self.semester

        if commit:
            instance.save()

        return instance
