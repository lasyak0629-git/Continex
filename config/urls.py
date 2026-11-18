# OWNER: Dev A
from apps.projects import team_views
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.handover import downloads

from apps.handover import views as handover_views
from apps.projects import views as project_views
from apps.projects import file_views
from apps.projects import stage_views, media_views

from django.urls import reverse_lazy
from apps.accounts import views as account_views

project_patterns = [
    path("<int:project_id>/upload/", project_views.upload, name="upload"),
    path("<int:project_id>/extract/", project_views.run_extract, name="extract"),
    path("<int:project_id>/handover/", handover_views.handover_page, name="handover"),
    path("<int:project_id>/handover/build/", handover_views.handover_build, name="handover_build"),
    path("new/", team_views.project_create, name="create"),
    path("<int:project_id>/team/", team_views.team, name="team"),
    path("<int:project_id>/analysis/", project_views.analysis_status, name="analysis_status"),
    path("<int:project_id>/send-to-leaver/", stage_views.send_to_leaver, name="send_to_leaver"),
    path("<int:project_id>/submit-to-manager/", stage_views.submit_to_manager, name="submit_to_manager"),
    path("<int:project_id>/gaps/<int:gap_id>/", stage_views.gap_answer, name="gap_answer"),
    path("<int:project_id>/handover/download/<str:fmt>/", downloads.handover_download, name="handover_download"),
    path("<int:project_id>/sources/<int:source_id>/transcript/", media_views.transcript, name="transcript"),
    path("<int:project_id>/sources/<int:source_id>/file/", file_views.source_file, name="source_file"),
    path("<int:project_id>/extend-retention/", team_views.extend_retention, name="extend_retention"),
    path("<int:project_id>/delete/", team_views.delete_project, name="delete_project"),
    path("<int:project_id>/handover/receipt/", handover_views.handover_receipt, name="handover_receipt"),
]

urlpatterns = [
    path("", project_views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("verify/<str:token>/", account_views.verify_email, name="verify_email"),
    path("verify-email/", account_views.verify_notice, name="verify_notice"),
    path("resend-verification/", account_views.resend_verification, name="resend_verification"),
    path("terms/", account_views.terms, name="terms"),
    path("privacy/", account_views.privacy, name="privacy"),
    path("invite/<str:token>/", team_views.accept_invite, name="accept_invite"),
    path("signup/", account_views.signup, name="signup"),
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="auth/password_reset_form.html",
        email_template_name="auth/password_reset_email.txt",
        subject_template_name="auth/password_reset_subject.txt",
        success_url=reverse_lazy("password_reset_done")), name="password_reset"),
    path("password-reset/sent/", auth_views.PasswordResetDoneView.as_view(
        template_name="auth/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="auth/password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete")), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="auth/password_reset_complete.html"), name="password_reset_complete"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("projects/<int:project_id>/review/", include("apps.review.urls")),
    path("projects/", include((project_patterns, "projects"))),
]