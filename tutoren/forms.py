from django import forms

from tutoren.models import Tutor


class TutorenAdminForm(forms.ModelForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "registration_time"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(TutorenAdminForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TutorenAdminForm, self).save(False)
        instance.semester = self.semester

        if commit:
            instance.save()

        return instance


class TutorenForm(TutorenAdminForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "status", "registration_time"]
