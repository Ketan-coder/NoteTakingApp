from django.urls import path
from django.views.generic import TemplateView

from . import views
from .views import (CustomPasswordResetCompleteView,
                    CustomPasswordResetConfirmView,
                    CustomPasswordResetDoneView, CustomPasswordResetView)

urlpatterns = [
    # path("", views.index, name="index"),
    path("update_user/", views.updateUser, name="update_user"),
    path("login/", views.login_form, name="login"),
    path("logout/", views.logout_form, name="logout"),
    path("register/", views.registeration_form, name="register"),
    path("signup/", views.register_view, name="signup"),
    path("check-username/", views.check_username, name="check_username"),
    path(
        "confirm-email/<str:token>/",
        views.email_confirmation_view,
        name="email_confirmation",
    ),
    path("update-email/", views.update_email_request, name="update_email"),
    path(
        "confirm-new-email/<uuid:token>/<str:new_email>/",
        views.confirm_new_email,
        name="confirm_new_email",
    ),
    path("setup-profile/", views.profile_setup_view, name="profile_setup"),
    path(
        "email-confirmation-pending/",
        TemplateView.as_view(template_name="email_pending.html"),
        name="email_confirmation_pending",
    ),
    path("password-reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
