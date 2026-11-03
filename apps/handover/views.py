# OWNER: Dev B

# Message from Dev A:
# Handover backend is ready. In views.py call only these: 
# build_handover(project, request.user) (from apps.handover.builder) builds it. It raises HandoverBlocked with .reasons (a list of strings) if blockers or pending items remain, so show those reasons. 
# handover_for_user(request.user, handover) (from apps.handover.role_filter) returns the data for your template: leaver, leave_date, role, sections (each has title, entries, hidden), warnings, hidden_total.
# Never read handover.content directly in a view or template. It’s the unfiltered version, and the filter is what protects restricted data.
# Use @project_role_required("viewer") from apps.accounts.decorators on the view.