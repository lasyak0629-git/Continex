# Dev A created
from django.urls import path
from . import views

app_name = "review"
urlpatterns = [
    path("", views.review_home, name="home"),
    path("item/<int:item_id>/edit/", views.item_edit, name="item_edit"),
    path("item/<int:item_id>/<str:action>/", views.item_action, name="item_action"),
    path("rerun/", views.rerun, name="rerun"),
]