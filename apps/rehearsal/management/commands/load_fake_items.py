# Dev A created this file 
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.extraction.models import ExtractedItem
from apps.extraction.schemas import ExtractedItemSchema
from apps.projects.models import Project, Source


class Command(BaseCommand):
    help = "Load demo_data/fake_extracted_items.json into a project"

    def add_arguments(self, parser):
        parser.add_argument("project_id", type=int)

    def handle(self, *args, **opts):
        project = Project.objects.get(pk=opts["project_id"])
        path = Path(settings.BASE_DIR) / "demo_data" / "fake_extracted_items.json"
        for d in json.loads(path.read_text(encoding="utf-8")):
            verified = d.pop("quote_verified", True)  # planted bad quotes set this to false
            s = ExtractedItemSchema.from_dict(d)
            source, _ = Source.objects.get_or_create(
                project=project, name=s.source_name, defaults={"uploaded_by": project.created_by}
            )
            item = ExtractedItem.from_schema(project, source, s)
            item.quote_verified = verified
            item.save()
        self.stdout.write(self.style.SUCCESS("Loaded fake items."))