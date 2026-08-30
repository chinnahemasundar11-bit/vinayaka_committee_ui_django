from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("verify-mfa-otp/", views.verify_mfa_otp_view, name="verify_mfa_otp"),
    path("register/", views.register_view, name="register"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("verify-forgot-otp/", views.verify_forgot_otp_view, name="verify_forgot_otp"),
    path("logout/", views.logout_view, name="logout"),
]
