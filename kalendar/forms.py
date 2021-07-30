from typing import List

from django import forms

from kalendar.models import Date


class DateForm(forms.ModelForm):
    class Meta:
        model = Date
        exclude: List[str] = ["name"]

    def __init__(self, *args, **kwargs):
        self.date_group = kwargs.pop("date_group")
        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True) -> Date:
        date: Date = super().save(commit=False)
        date.group = self.date_group
        if commit:
            date.save()
        return date
