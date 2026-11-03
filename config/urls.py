# OWNER: Dev A

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.projects import views as project_views

project_patterns = [
    path("<int:project_id>/upload/", project_views.upload, name="upload"),
    path("eval/", project_views.eval_results, name="eval"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("projects/<int:project_id>/review/", include("apps.review.urls")),
    path("projects/", include((project_patterns, "projects"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)