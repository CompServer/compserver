from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("", views.BracketView, name="bracket"),
    path("competitions", views.competitions, name="competitions"),
    path("competitions/<int:pk>", views.not_implemented, name="competition")
]
