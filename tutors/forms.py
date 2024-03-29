from bootstrap_datepicker_plus.widgets import DatePickerInput, DateTimePickerInput
from django import forms
from django.utils.translation import gettext_lazy as _

from settool_common.forms import CommonParticipantForm, SemesterBasedForm, SemesterBasedModelForm
from settool_common.models import Subject
from tutors.models import (
    Answer,
    Event,
    MailTutorTask,
    Question,
    Settings,
    SubjectTutorCountAssignment,
    Task,
    Tutor,
    TutorAssignment,
    TutorMail,
)


class TutorAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "registration_time", "answers"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birthday"].required = False
        self.fields["matriculation_number"].required = False

    def clean(self):
        super().clean()
        mail = self.cleaned_data.get("email")
        if mail:
            tutors = Tutor.objects.filter(semester=self.semester, email=mail)
            if tutors.count() > 0 and tutors.first().id != self.instance.id:
                self.add_error("email", _("The email address is already in use."))

        matriculation_number = self.cleaned_data.get("matriculation_number")
        if matriculation_number:
            tutors = Tutor.objects.filter(semester=self.semester, matriculation_number=matriculation_number)
            if tutors.count() > 0 and tutors.first().id != self.instance.id:
                self.add_error(
                    "matriculation_number",
                    _("The matriculation number is already in use."),
                )


class TutorForm(CommonParticipantForm):
    class Meta:
        model = Tutor
        exclude = ["semester", "status", "registration_time", "answers"]
        widgets = {
            "birthday": DatePickerInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birthday"].required = False
        self.fields["matriculation_number"].required = False

    field_order = ["first_name", "last_name", "email", "ects", "birthday", "matriculation_number"]

    def clean(self):
        super().clean()
        ects = self.cleaned_data.get("ects")

        if ects:
            self.validate_required_field(cleaned_data=self.cleaned_data, field_name="birthday")
            self.validate_required_field(cleaned_data=self.cleaned_data, field_name="matriculation_number")
        else:
            self.cleaned_data["birthday"] = None
            self.cleaned_data["matriculation_number"] = None

        return self.cleaned_data

    def validate_required_field(self, cleaned_data, field_name, message=""):
        if not message:
            message = _("This field is required")
        if field_name in cleaned_data and cleaned_data[field_name] is None:
            self._errors[field_name] = self.error_class([message])
            del cleaned_data[field_name]


class CollaboratorForm(TutorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ects"].label = _("I want to receive ECTS for my work as a SET-Colaborator.")


class EventAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Event
        exclude = ["semester", "name", "description", "meeting_point"]
        widgets = {
            "begin": DateTimePickerInput(),
            "end": DateTimePickerInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description_de"].required = False
        self.fields["description_en"].required = False

    def save(self, commit=True):
        instance = super().save(False)
        instance.save()

        if "subjects" in self.changed_data:
            final_subjects = self.cleaned_data["subjects"].all()
            initial_subjects = self.initial["subjects"] if "subjects" in self.initial else []

            # create and save new members
            for subject in final_subjects:
                if subject not in initial_subjects:
                    instance.subjects.add(subject)

            # delete old members that were removed from the form
            for subject in initial_subjects:
                if subject not in final_subjects:
                    instance.subjects.remove(subject)

        return instance

    def clean(self):
        cleaned_data = super().clean()

        begin = cleaned_data.get("begin")
        end = cleaned_data.get("end")
        if begin and end and end <= begin:
            msg = _("Begin time must be before end time.")
            self.add_error("begin", msg)
            self.add_error("end", msg)
        return cleaned_data


class TaskAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Task
        exclude = ["semester", "name", "description", "meeting_point", "tutors"]
        widgets = {
            "begin": DateTimePickerInput(),
            "end": DateTimePickerInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description_de"].required = False
        self.fields["description_en"].required = False

    def save(self, commit=True):
        instance = super().save(False)
        instance.save()

        if "allowed_subjects" in self.changed_data:
            final_subjects = self.cleaned_data["allowed_subjects"].all()
            initial_subjects = self.initial["allowed_subjects"] if "allowed_subjects" in self.initial else []

            # create and save new members
            for subject in final_subjects:
                if subject not in initial_subjects:
                    instance.allowed_subjects.add(subject)

            # delete old members that were removed from the form
            for subject in initial_subjects:
                if subject not in final_subjects:
                    instance.allowed_subjects.remove(subject)

        if "requirements" in self.changed_data:
            final_requirements = self.cleaned_data["requirements"].all()
            initial_requirements = self.initial["requirements"] if "requirements" in self.initial else []

            # create and save new members
            for subject in final_requirements:
                if subject not in initial_requirements:
                    instance.requirements.add(subject)

            # delete old members that were removed from the form
            for subject in initial_requirements:
                if subject not in final_requirements:
                    instance.requirements.remove(subject)

        return instance

    def clean(self):
        cleaned_data = super().clean()

        begin = cleaned_data.get("begin")
        end = cleaned_data.get("end")
        if begin and end and end <= begin:
            msg = _("Begin time must be before end time.")
            self.add_error("begin", msg)
            self.add_error("end", msg)
        return cleaned_data


class TaskAssignmentForm(SemesterBasedModelForm):
    class Meta:
        model = Task
        fields = ["tutors"]

    def save(self, commit=True):
        instance: Task = super().save(commit=False)
        if "tutors" in self.changed_data:
            final_tutors = self.cleaned_data["tutors"].all()
            initial_tutors = self.initial["tutors"] if "tutors" in self.initial else []

            # create and save new members
            for tutor in final_tutors:
                if tutor not in initial_tutors:
                    TutorAssignment.objects.create(tutor=tutor, task=instance)

            # delete old members that were removed from the form
            for tutor in initial_tutors:
                if tutor not in final_tutors:
                    TutorAssignment.objects.get(tutor=tutor, task=instance).delete()


class RequirementAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Question
        exclude = ["semester", "question"]


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        exclude = ["tutor"]
        widgets = {
            "question": forms.HiddenInput,
            "answer": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["answer"].label = Question.objects.get(pk=self.initial.get("question"))
        self.fields["answer"].choices = self.fields["answer"].choices[1:]


class SettingsAdminForm(SemesterBasedModelForm):
    class Meta:
        model = Settings
        exclude = ["semester"]
        widgets = {
            "open_registration": DateTimePickerInput(),
            "close_registration": DateTimePickerInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        begin = cleaned_data.get("open_registration")
        end = cleaned_data.get("close_registration")
        if begin and end and end <= begin:
            msg = _("Begin time must be before end time.")
            self.add_error("open_registration", msg)
            self.add_error("close_registration", msg)
        return cleaned_data


class TutorMailAdminForm(SemesterBasedForm):
    mail_template = forms.ModelChoiceField(label="Mail Template", queryset=TutorMail.objects.all(), required=True)

    tutors = forms.ModelMultipleChoiceField(
        label=_("Tutors (selected have not yet received this email)"),
        widget=forms.CheckboxSelectMultiple,
        queryset=Tutor.objects.none(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        tutors = kwargs.pop("tutors")
        template = kwargs.pop("template")
        super().__init__(*args, **kwargs)

        self.fields["tutors"].queryset = tutors
        self.fields["tutors"].initial = Tutor.objects.exclude(
            id__in=MailTutorTask.objects.filter(mail=template).values("tutor_id"),
        )
        self.fields["mail_template"].initial = template


class SubjectTutorCountAssignmentAdminForm(SemesterBasedModelForm):
    class Meta:
        model = SubjectTutorCountAssignment
        exclude = ["semester"]
        widgets = {
            "subject": forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["wanted"].label = Subject.objects.get(pk=self.initial.get("subject")).__str__()
        self.fields["waitlist"].label = _("Waiting List").__str__()


class TutorAcceptAdminForm(SemesterBasedForm):
    tutors = forms.ModelMultipleChoiceField(
        label=_("Tutors (selected will be accepted)"),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        queryset=Tutor.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        tutors = kwargs.pop("tutors")
        super().__init__(*args, **kwargs)

        self.fields["tutors"].queryset = tutors
        self.fields["tutors"].initial = tutors


class TutorDeclineAdminForm(SemesterBasedForm):
    tutors = forms.ModelMultipleChoiceField(
        label=_("Tutors (selected will be declined)"),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        queryset=Tutor.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        tutors = kwargs.pop("tutors")
        super().__init__(*args, **kwargs)

        self.fields["tutors"].queryset = tutors
        self.fields["tutors"].initial = tutors
