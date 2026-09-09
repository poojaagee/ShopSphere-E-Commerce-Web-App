from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path(
        "register/",
        views.register,
        name="register",
    ),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
        ),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "profile/",
        views.profile,
        name="profile",
    ),

    path(
        "addresses/add/",
        views.address_create,
        name="address_create",
    ),

    path(
        "addresses/<int:pk>/edit/",
        views.address_edit,
        name="address_edit",
    ),

    path(
        "addresses/<int:pk>/delete/",
        views.address_delete,
        name="address_delete",
    ),
]