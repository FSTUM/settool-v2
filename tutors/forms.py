from django import forms

from tutors.models import Tutor, Event, Task


class SemesterBasedForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(SemesterBasedForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(SemesterBasedForm, self).save(False)
        instance.semester = self.semester

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class TutorenAdminForm(SemesterBasedForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "registration_time"]


class TutorenForm(TutorenAdminForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "status", "registration_time"]


class EventAdminForm(SemesterBasedForm):
    class Meta:
        model = Event
        exclude = ["semester"]


class TaskAdminForm(SemesterBasedForm):
    class Meta:
        model = Task
        exclude = ["semester"]
