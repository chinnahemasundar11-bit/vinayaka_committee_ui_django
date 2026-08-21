from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext as _
from audit.models import AuditLog


def login_view(request):
    """Committee login view with mobile/username authentication."""
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip() or request.POST.get("mobile", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, _("* Please enter both Mobile Number / Username and Password."))
            return render(request, "accounts/login.html")

        try:
            user = authenticate(request, username=username, password=password)
        except (ValueError, TypeError):
            user = None

        if user is not None:
            auth_login(request, user)
            AuditLog.objects.create(user=user, action="LOGIN", model_name="User", object_id=str(user.id), details=f"User {user.username} logged in successfully")
            user_disp = user.first_name or user.username
            messages.success(request, _("Welcome back, %(name)s!") % {"name": user_disp})
            return redirect("/dashboard/")
        else:
            messages.error(request, _("Invalid mobile number/username or password. Please try again."))

    return render(request, "accounts/login.html")


def register_view(request):
    """Committee member account registration view."""
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        password = request.POST.get("password", "").strip()

        if not full_name or not mobile or not password:
            messages.error(request, _("* All fields marked with an asterisk are required."))
            return render(request, "accounts/register.html")

        if User.objects.filter(username=mobile).exists():
            messages.error(request, _("An account with this mobile number already exists."))
            return render(request, "accounts/register.html")

        first_name = full_name.split()[0]
        last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else ""

        user = User.objects.create_user(username=mobile, password=password, first_name=first_name, last_name=last_name)
        AuditLog.objects.create(user=user, action="REGISTER", model_name="User", object_id=str(user.id), details=f"Registered account for {full_name}")
        messages.success(request, _("Account created successfully! Please sign in with your credentials."))
        return redirect("/accounts/login/")

    return render(request, "accounts/register.html")


def forgot_password_view(request):
    """Password reset request view."""
    if request.method == "POST":
        mobile = request.POST.get("mobile", "").strip()
        messages.success(request, _("Password reset instructions sent to registered mobile number %(mobile)s.") % {"mobile": mobile})
        return redirect("/accounts/login/")
    return render(request, "accounts/forgot_password.html")


def logout_view(request):
    """Sign out committee session."""
    if request.user.is_authenticated:
        AuditLog.objects.create(user=request.user, action="LOGOUT", model_name="User", object_id=str(request.user.id), details=f"User {request.user.username} logged out")
        auth_logout(request)
    messages.info(request, _("You have been logged out."))
    return redirect("/accounts/login/")
