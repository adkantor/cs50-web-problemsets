from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("wiki/<str:title>", views.entry, name="entry"),
    path("search", views.search, name="search"),
    path("random_page", views.random_page, name="random_page"),
    path("new", views.create_new_page, name="create_new_page"),
    path("edit", views.edit_page, name="edit_page"),
]
