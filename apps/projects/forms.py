from django import forms
from .models import Project
from .scan import scan
from .validators import check_content

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
    ALLOWED_EXT = {".txt", ".md", ".csv", ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".webp",
                   ".mp3", ".wav", ".ogg", ".aac", ".flac"}
    MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".ogg", ".aac", ".flac"}
    MAX_MB, MAX_MEDIA_MB, MAX_FILES = 10, 15, 20

    def clean_files(self):
        files = self.cleaned_data["files"]
        if len(files) > self.MAX_FILES:
            raise forms.ValidationError(f"Upload at most {self.MAX_FILES} files at a time.")
        for f in files:
            ext = "." + f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
            if ext not in self.ALLOWED_EXT:
                raise forms.ValidationError(
                    f"'{f.name}' is not supported. Use: .txt, .md, .csv, .docx or .pdf." "images (.png, .jpg, .jpeg, .webp) or audio (.mp3, .wav, .ogg, .aac, .flac).")
            limit = self.MAX_MEDIA_MB if ext in self.MEDIA_EXT else self.MAX_MB
            if f.size > limit * 1024 * 1024:
                raise forms.ValidationError(f"'{f.name}' is larger than {limit} MB.")
            problem = check_content(f, ext)
            if problem:
                raise forms.ValidationError(f"'{f.name}' {problem}.")
            problem = scan(f)
            if problem:
                raise forms.ValidationError(f"'{f.name}' {problem}")
        return files

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