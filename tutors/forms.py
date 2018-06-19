from uuid import UUID

from django import forms
from django.utils import six

from common.forms import SemesterBasedForm
from common.models import Mail
from tutors.models import Tutor, Event, Task, TutorAssignment, Question, Answer, Settings


class TutorAdminForm(SemesterBasedForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "registration_time", "answers"]


class TutorForm(TutorAdminForm):
    dsgvo = forms.BooleanField(required=True)

    class Meta:
        model = Tutor
        exclude = ["semester", "status", "registration_time", "answers"]

    def save(self, commit=True):
        instance = super(TutorForm, self).save(False)
        instance.save()

        if 'answers' in self.changed_data:
            final_answers = self.cleaned_data['answers'].all()
            initial_answers = self.initial['answers'] if 'answers' in self.initial else []

            # create and save new members
            for answer in final_answers:
                if answer not in initial_answers:
                    instance.answers.add(answer)

            # delete old members that were removed from the form
            for answer in initial_answers:
                if answer not in final_answers:
                    instance.answers.remove(answer)
        return instance


class EventAdminForm(SemesterBasedForm):
    class Meta:
        model = Event
        exclude = ["semester", "name", "description", "meeting_point"]

    def save(self, commit=True):
        instance = super(EventAdminForm, self).save(False)
        instance.save()

        if 'subjects' in self.changed_data:
            final_subjects = self.cleaned_data['subjects'].all()
            initial_subjects = self.initial['subjects'] if 'subjects' in self.initial else []

            # create and save new members
            for subject in final_subjects:
                if subject not in initial_subjects:
                    instance.subjects.add(subject)

            # delete old members that were removed from the form
            for subject in initial_subjects:
                if subject not in final_subjects:
                    instance.subjects.remove(subject)

        return instance


class TaskAdminForm(SemesterBasedForm):
    class Meta:
        model = Task
        exclude = ["semester", "name", "description", "meeting_point", "tutors"]

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

        if 'requirements' in self.changed_data:
            final_requirements = self.cleaned_data['requirements'].all()
            initial_requirements = self.initial['requirements'] if 'requirements' in self.initial else []

            # create and save new members
            for subject in final_requirements:
                if subject not in initial_requirements:
                    instance.requirements.add(subject)

            # delete old members that were removed from the form
            for subject in initial_requirements:
                if subject not in final_requirements:
                    instance.requirements.remove(subject)

        return instance


class TaskAssignmentForm(SemesterBasedForm):
    class Meta:
        model = Task
        fields = ["tutors"]

    def save(self, commit=True):
        instance = super(TaskAssignmentForm, self).save(False)
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


class RequirementAdminForm(SemesterBasedForm):
    class Meta:
        model = Question
        exclude = ["semester", "question"]


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        exclude = ["tutor"]
        readonly_fields = ('question',)
        widgets = {
            'answer': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super(AnswerForm, self).__init__(*args, **kwargs)
        for field in (field for name, field in six.iteritems(self.fields) if
                      name in self.Meta.readonly_fields):
            field.widget.attrs['disabled'] = True
            field.required = False

    def clean(self):
        data = super(AnswerForm, self).clean()
        for name, field in six.iteritems(self.fields):
            if name in self.Meta.readonly_fields:
                if isinstance(self.initial[name], UUID):
                    data[name] = Question.objects.get(pk=self.initial[name])
                else:
                    data[name] = self.initial[name]


class SettingsAdminForm(SemesterBasedForm):
    class Meta:
        model = Settings
        exclude = ["semester", ]


class TaskMailAdminForm(forms.Form):
    tutors = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=None, required=True)
    mail_template = forms.ModelChoiceField(label='Mail Template', queryset=Mail.objects.all(), required=True)

    def __init__(self, *args, **kwargs):
        task = kwargs.pop('task')
        settings = kwargs.pop('settings')
        super(TaskMailAdminForm, self).__init__(*args, **kwargs)

        self.fields["tutors"].queryset = task.tutors.all()
        self.fields["tutors"].initial = task.tutors.all()
        self.fields["mail_template"].initial = settings.mail_task
