# OWNER: Dev A
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404

from .permissions import ROLE_RANK, get_role


def project_role_required(min_role):
    """Only project members with at least `min_role` get in."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, project_id, *args, **kwargs):
            from apps.projects.models import Project  # avoid circular import
            project = get_object_or_404(Project, pk=project_id)
            role = get_role(request.user, project)
            if role is None:
                raise Http404  # don't reveal that the project exists
            if ROLE_RANK[role] < ROLE_RANK[min_role]:
                return HttpResponseForbidden("Your role cannot do this.")
            request.project = project
            request.project_role = role
            return view(request, project_id, *args, **kwargs)
        return wrapper
    return decorator