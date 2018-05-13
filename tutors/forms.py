from django import forms

from tutors.models import Tutor, Event, Task, TutorAssignment


class SemesterBasedForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(SemesterBasedForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(SemesterBasedForm, self).save(False)
        instance.semester = self.semester

        if commit:
            instance.save()

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

    def save(self, commit=True):
        instance = super(TaskAdminForm, self).save(False)
        instance.save()

        if 'allowed_subjects' in self.changed_data:
            final_subjects = self.cleaned_data['allowed_subjects'].all()
            initial_subjects = self.initial['allowed_subjects'] if 'allowed_subjects' in self.initial else []

            # create and save new members
            for subject in final_subjects:
                if subject not in initial_subjects:
                    instance.allowed_subjects.add(subject)

            # delete old members that were removed from the form
            for subject in initial_subjects:
                if subject not in final_subjects:
                    instance.allowed_subjects.remove(subject)

        if 'tutors' in self.changed_data:
            final_tutors = self.cleaned_data['tutors'].all()
            initial_tutors = self.initial['tutors'] if 'tutors' in self.initial else []

            # create and save new members
            for tutor in final_tutors:
                if tutor not in initial_tutors:
                    TutorAssignment.objects.create(tutor=tutor, task=instance)

            # delete old members that were removed from the form
            for tutor in initial_tutors:
                if tutor not in final_tutors:
                    TutorAssignment.objects.filter(tutor=tutor, task=instance).delete()

        return instance
