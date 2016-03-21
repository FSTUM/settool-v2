from django import forms

from .models import Participant

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        exclude = ["time"]

    def __init__(self, *args, **kwargs):
        tours = kwargs.pop('tours')
        super(ParticipantForm, self).__init__(*args, **kwargs)
        self.fields['tour'].queryset = tours
