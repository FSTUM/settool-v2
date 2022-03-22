from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django import forms

from kalendar.models import Date


class DateForm(forms.ModelForm):
    class Meta:
        model = Date
        exclude: list[str] = []
        widgets = {
            "date": DateTimePickerInput(format="%Y-%m-%d %H:%M"),
        }

    def __init__(self, *args, **kwargs):
        self.date_group = kwargs.pop("date_group")
        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True) -> Date:
        date: Date = super().save(commit=False)
        date.group = self.date_group
        if commit:
            date.save()
        return date
