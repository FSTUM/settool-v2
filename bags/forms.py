from django import forms

from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ["semester"]

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(CompanyForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(CompanyForm, self).save(False)
        instance.semester = self.semester
        if commit:
            instance.save()
        return instance
