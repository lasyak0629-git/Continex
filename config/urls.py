# OWNER: Dev A

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("projects/<int:project_id>/review/", include("apps.review.urls")),
]