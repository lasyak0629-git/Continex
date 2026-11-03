# OWNER: Dev B
# OWNER: Dev B
from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)]


ACCESS_CHOICES = [
    ("public", "Everyone on the project"),
    ("internal", "Team members and above"),
    ("restricted", "Leads only (never sent to the AI)"),
]


class UploadForm(forms.Form):
    files = MultipleFileField()
    access_level = forms.ChoiceField(choices=ACCESS_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))