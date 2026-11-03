# created by Dev A on 2024-06-15
from django.contrib import admin
from .models import Project, Membership, Source

admin.site.register(Project)
admin.site.register(Membership)
admin.site.register(Source)