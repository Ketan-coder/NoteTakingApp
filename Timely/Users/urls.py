from django.urls import path
from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path("update_user/", views.updateUser, name="update_user"),
    path("login/", views.login_form, name="login"),
    path("logout/", views.logout_form, name="logout"),
    path("register/", views.registeration_form, name="register"),
]
