# OWNER: Dev A
ROLE_RANK = {"viewer": 1, "member": 2, "manager": 3, "owner": 4}
SENSITIVITY_MIN_RANK = {"public": 1, "internal": 2, "restricted": 3}


def get_role(user, project):
    if not user.is_authenticated:
        return None
    m = project.memberships.filter(user=user).first()
    return m.role if m else None


def can_view(user, source):
    """Return True only if the user's role allows seeing this source."""
    role = get_role(user, source.project)
    if role is None:
        return False
    return ROLE_RANK[role] >= SENSITIVITY_MIN_RANK[source.sensitivity]