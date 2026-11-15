from django import forms
from .models import Project

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

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "project_type", "leaver_name", "leave_date")
        labels = {
            "name": "Project name",
            "description": "What is this project about?",
            "project_type": "Type",
            "leaver_name": "Who is leaving?",
            "leave_date": "Last working day",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "leave_date": forms.DateInput(attrs={"type": "date"}),
        }


class InviteForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[
        ("leaver", "Leaving person (uploads and does the first review)"),
        ("viewer", "Viewer / newcomer (views and downloads the handover)"),
        ("manager", "Manager (full control)"),
    ])