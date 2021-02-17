from typing import List

from django import forms
from django.utils.translation import ugettext_lazy as _

from bags.models import BagMail
from fahrt.models import FahrtMail
from guidedtours.models import TourMail
from tutors.models import TutorMail

from .models import Mail


class SemesterBasedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super().__init__(*args, **kwargs)


class SemesterBasedModelForm(SemesterBasedForm, forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(False)
        instance.semester = self.semester
        if commit:
            instance.save()
        return instance


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude: List[str] = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        new_choices = self._get_choices_for_user()
        self.fields["sender"].choices = new_choices
        self.fields["sender"].initial = new_choices[0]

    def get_mails(self):
        full_choices = dict(Mail.FROM_CHOICES)

        mails = {}
        if TutorMail.check_perm(self.user):
            mails[(Mail.SET_TUTOR, full_choices[Mail.SET_TUTOR])] = TutorMail
        if BagMail.check_perm(self.user):
            mails[(Mail.SET_BAGS, full_choices[Mail.SET_BAGS])] = BagMail
        if TourMail.check_perm(self.user):
            mails[(Mail.SET, full_choices[Mail.SET])] = TourMail
        if FahrtMail.check_perm(self.user):
            mails[(Mail.SET_FAHRT, full_choices[Mail.SET_FAHRT])] = FahrtMail
        return mails

    def _get_choices_for_user(self):
        mails = self.get_mails()
        return list(mails.keys())

    def save(self, commit=True):
        mail: Mail = super().save(commit=False)
        list_of_poss_senders_for_user = [sender for (sender, _), _ in self.get_mails()]
        if mail.sender not in list_of_poss_senders_for_user:
            raise PermissionError("user does not have the Permisson to save this kind of mail")
        if self.instance:
            mail.delete()  # we possibly edited the sender
        if mail.sender == Mail.SET_TUTOR:
            cls = TourMail
        elif mail.sender == Mail.SET_BAGS:
            cls = BagMail
        elif mail.sender == Mail.SET:
            cls = TourMail
        else:
            cls = FahrtMail
        return cls.objects.create(
            pk=mail.pk,
            sender=mail.sender,
            text=mail.text,
            comment=mail.comment,
            subject=mail.subject,
        )


class SelectMailForm(forms.Form):
    mail = forms.ModelChoiceField(
        queryset=Mail.objects.all(),
        label=_("Email template:"),
    )


def produce_csv_file_upload_field(fields):
    return forms.FileField(
        allow_empty_file=False,
        label=_(
            "Upload a csv-file in exel-formatting. " "(Column-order: {fields}. First line is header.)",
        ).format(fields=fields),
    )


class CSVFileUploadForm(forms.Form):
    file = produce_csv_file_upload_field("sender, subject, text, comment")


class CommonParticipantForm(SemesterBasedModelForm):
    dsgvo = forms.BooleanField(
        label=_("I accept the terms and conditions of the following privacy policy:"),
        required=True,
    )
