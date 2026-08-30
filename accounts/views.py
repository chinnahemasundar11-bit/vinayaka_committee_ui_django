import os
import secrets
import re
import urllib.request
import urllib.parse
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from audit.models import AuditLog
from administration.models import SiteSetting


def generate_otp():
    """Generate a secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def send_otp_notification(user, otp_code, purpose="Authentication"):
    """
    Dispatches OTP notification via Real-Time Channels:
    - HTTP SMS Gateway (Fast2SMS / Twilio / SMSIndiaHub / MSG91 if SMS_API_KEY configured)
    - Real Email (via Django send_mail)
    - WhatsApp 1-Click Dispatch Link
    - Console Output & NotificationLog Audit Trail
    """
    phone = str(user.username).strip()
    user_email = getattr(user, "email", None) or f"{phone}@vinayaka.org"
    site_name_obj = SiteSetting.objects.filter(key="SITE_NAME").first()
    site_name = site_name_obj.value if site_name_obj else "Vinayaka Youth Committee"

    subject = f"[{site_name}] Your 6-Digit OTP Code for {purpose}"
    message_body = (
        f"Dear {user.first_name or user.username},\n\n"
        f"Your 6-digit One-Time Password (OTP) for {purpose} is:\n\n"
        f"   {otp_code}\n\n"
        f"This code is valid for 10 minutes. Please do not share this OTP code with anyone.\n\n"
        f"Regards,\n"
        f"{site_name} Security Team"
    )

    # 1. Real Email Dispatch via Django send_mail
    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@vinayaka.org"),
            recipient_list=[user_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"OTP Email dispatch exception: {e}")

    # 2. Free Mobile SMS Dispatch Channels (Fast2SMS Free Tier / Free Android Phone SMS Gateway)
    sms_api_key = getattr(settings, "SMS_API_KEY", "") or os.environ.get("SMS_API_KEY", "") or os.environ.get("FAST2SMS_API_KEY", "")
    android_gateway_url = getattr(settings, "ANDROID_SMS_GATEWAY_URL", "") or os.environ.get("ANDROID_SMS_GATEWAY_URL", "")
    whatsapp_bot_url = getattr(settings, "WHATSAPP_BOT_URL", "") or os.environ.get("WHATSAPP_BOT_URL", "")
    sms_status = "SENT"

    # Fast2SMS Free API Call
    if sms_api_key and len(phone) >= 10:
        try:
            sms_url = f"https://www.fast2sms.com/dev/bulkV2?authorization={sms_api_key}&route=otp&variables_values={otp_code}&flash=0&numbers={phone}"
            req = urllib.request.Request(sms_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"Real Mobile SMS dispatched to {phone}: HTTP Status {response.status}")
        except Exception as sms_err:
            print(f"SMS Gateway dispatch exception: {sms_err}")
            sms_status = "PENDING_GATEWAY"

    # Free Android Phone SMS Gateway API Call
    if android_gateway_url and len(phone) >= 10:
        try:
            gw_url = android_gateway_url.format(phone=phone, code=otp_code, purpose=urllib.parse.quote(purpose))
            req = urllib.request.Request(gw_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"Android Gateway SMS dispatched to {phone}: HTTP Status {response.status}")
        except Exception as gw_err:
            print(f"Android Gateway exception: {gw_err}")

    # Free Local WhatsApp Bot API Microservice Call
    if whatsapp_bot_url and len(phone) >= 10:
        try:
            wb_url = whatsapp_bot_url.format(phone=phone, code=otp_code, purpose=urllib.parse.quote(purpose))
            req = urllib.request.Request(wb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"WhatsApp Bot message dispatched to {phone}: HTTP Status {response.status}")
        except Exception as wb_err:
            print(f"WhatsApp Bot exception: {wb_err}")

    # 3. WhatsApp 1-Click Dispatch Link Generation
    wa_text = urllib.parse.quote(f"🚩 *{site_name.upper()}* 🚩\n*SECURITY OTP CODE*\n\nYour 6-digit OTP for *{purpose}* is: *{otp_code}*\n\nValid for 10 minutes.")
    clean_wa_phone = phone if phone.startswith("91") else f"91{phone}"
    wa_dispatch_url = f"https://api.whatsapp.com/send?phone={clean_wa_phone}&text={wa_text}"

    # 4. Console Output for Local Development / Free Testing
    print(f"\n==========================================")
    print(f" [OTP NOTIFICATION DISPATCH] User: {user.username} | Code: {otp_code} | Purpose: {purpose}")
    print(f" WhatsApp URL: {wa_dispatch_url}")
    print(f"==========================================\n")

    # 5. Log into NotificationLog audit trail
    from audit.notifications import log_notification
    log_notification(
        recipient_phone=phone,
        recipient_name=user.get_full_name() or user.username,
        channel="OTP",
        purpose=f"OTP_{purpose.upper().replace(' ', '_')}",
        message_body=message_body,
        dispatch_url=wa_dispatch_url,
        status=sms_status,
        user=user if user.is_authenticated else None
    )


def login_view(request):
    """Committee login view with optional MFA OTP verification."""
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
            # Check Site Setting for MFA_ENABLED
            mfa_setting = SiteSetting.objects.filter(key="MFA_ENABLED").first()
            is_mfa_enabled = mfa_setting.value.lower() == "true" if mfa_setting else False

            if is_mfa_enabled:
                otp_code = generate_otp()
                expiry = (timezone.now() + timedelta(minutes=10)).timestamp()
                request.session["mfa_user_id"] = user.id
                request.session["mfa_otp"] = otp_code
                request.session["mfa_expiry"] = expiry
                
                send_otp_notification(user, otp_code, purpose="MFA Login Verification")
                messages.info(request, _("MFA Enabled: A 6-digit OTP code has been sent to your registered mobile number."))
                return redirect("/accounts/verify-mfa-otp/")
            else:
                auth_login(request, user)
                AuditLog.objects.create(user=user, action="LOGIN", model_name="User", object_id=str(user.id), details=f"User {user.username} logged in successfully")
                user_disp = user.first_name or user.username
                messages.success(request, _("Welcome back, %(name)s!") % {"name": user_disp})
                return redirect("/dashboard/")
        else:
            messages.error(request, _("Invalid mobile number/username or password. Please try again."))

    return render(request, "accounts/login.html")


def verify_mfa_otp_view(request):
    """Verify 2-Step MFA OTP Code for Login."""
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    mfa_user_id = request.session.get("mfa_user_id")
    mfa_otp = request.session.get("mfa_otp")
    mfa_expiry = request.session.get("mfa_expiry")

    if not mfa_user_id or not mfa_otp:
        messages.error(request, _("Session expired or invalid login request. Please login again."))
        return redirect("/accounts/login/")

    user = User.objects.filter(id=mfa_user_id).first()
    if not user:
        messages.error(request, _("Invalid user session."))
        return redirect("/accounts/login/")

    if request.method == "POST":
        action = request.POST.get("action", "verify")
        
        if action == "resend":
            otp_code = generate_otp()
            request.session["mfa_otp"] = otp_code
            request.session["mfa_expiry"] = (timezone.now() + timedelta(minutes=10)).timestamp()
            send_otp_notification(user, otp_code, purpose="MFA Login Verification (Resent)")
            messages.success(request, _("A new 6-digit OTP code has been sent to your registered mobile number."))
            return render(request, "accounts/verify_mfa_otp.html", {"user_obj": user})

        otp_input = request.POST.get("otp_code", "").strip()

        if mfa_expiry and timezone.now().timestamp() > mfa_expiry:
            messages.error(request, _("OTP code has expired. Please click 'Resend OTP' to receive a new code."))
            return render(request, "accounts/verify_mfa_otp.html", {"user_obj": user})

        if otp_input == mfa_otp:
            for k in ["mfa_user_id", "mfa_otp", "mfa_expiry"]:
                request.session.pop(k, None)
            
            auth_login(request, user)
            AuditLog.objects.create(user=user, action="LOGIN_MFA", model_name="User", object_id=str(user.id), details=f"User {user.username} logged in successfully via 2-Step MFA OTP")
            user_disp = user.first_name or user.username
            messages.success(request, _("MFA Verification successful. Welcome back, %(name)s!") % {"name": user_disp})
            return redirect("/dashboard/")
        else:
            messages.error(request, _("Invalid OTP code. Please enter the correct 6-digit code."))

    return render(request, "accounts/verify_mfa_otp.html", {"user_obj": user})


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
    """Password reset request view sending OTP verification code."""
    if request.method == "POST":
        input_identifier = request.POST.get("mobile", "").strip() or request.POST.get("email", "").strip()

        if not input_identifier:
            messages.error(request, _("* Please enter your registered Mobile Number or Email address."))
            return render(request, "accounts/forgot_password.html")

        # 1. Exact match by username or email
        user = User.objects.filter(Q(username__iexact=input_identifier) | Q(email__iexact=input_identifier)).first()

        # 2. Clean phone number lookup (+91 / 91 / spaces / hyphens)
        if not user:
            clean_num = re.sub(r"\D", "", input_identifier)
            if clean_num.startswith("91") and len(clean_num) == 12:
                clean_num = clean_num[2:]

            if len(clean_num) >= 8:
                user = User.objects.filter(Q(username__icontains=clean_num) | Q(email__icontains=clean_num)).first()
                if not user:
                    from members.models import Member
                    m = Member.objects.filter(mobile_number__icontains=clean_num, is_deleted=False).first()
                    if m:
                        user = User.objects.filter(Q(username=m.mobile_number) | Q(id=m.id)).first()

                # Prefix & Suffix match
                if not user and len(clean_num) >= 10:
                    user = User.objects.filter(username__startswith=clean_num[:4], username__endswith=clean_num[-4:]).first()

                # If a valid 10-digit mobile number is entered but no User object exists yet, auto-provision user
                if not user and len(clean_num) == 10:
                    user = User.objects.create_user(username=clean_num, email=f"{clean_num}@vinayaka.org", first_name="Committee Member")

        if user:
            otp_code = generate_otp()
            expiry = (timezone.now() + timedelta(minutes=10)).timestamp()
            request.session["reset_user_id"] = user.id
            request.session["reset_otp"] = otp_code
            request.session["reset_expiry"] = expiry
            
            send_otp_notification(user, otp_code, purpose="Password Reset")
            messages.success(request, _("A 6-digit password reset OTP code has been sent to your registered mobile number."))
            return redirect("/accounts/verify-forgot-otp/")
        else:
            messages.error(request, _("No registered account found matching '%(input)s'.") % {"input": input_identifier})
            return render(request, "accounts/forgot_password.html")

    return render(request, "accounts/forgot_password.html")


def verify_forgot_otp_view(request):
    """Verify password reset OTP and set new password."""
    reset_user_id = request.session.get("reset_user_id")
    reset_otp = request.session.get("reset_otp")
    reset_expiry = request.session.get("reset_expiry")

    if not reset_user_id or not reset_otp:
        messages.error(request, _("Session expired or invalid reset request. Please initiate password reset again."))
        return redirect("/accounts/forgot-password/")

    user = User.objects.filter(id=reset_user_id).first()
    if not user:
        messages.error(request, _("User account not found."))
        return redirect("/accounts/forgot-password/")

    if request.method == "POST":
        action = request.POST.get("action", "verify")

        if action == "resend":
            otp_code = generate_otp()
            request.session["reset_otp"] = otp_code
            request.session["reset_expiry"] = (timezone.now() + timedelta(minutes=10)).timestamp()
            send_otp_notification(user, otp_code, purpose="Password Reset (Resent)")
            messages.success(request, _("A new 6-digit password reset OTP code has been sent to your registered mobile number."))
            return render(request, "accounts/verify_forgot_otp.html", {"user_obj": user})

        otp_input = request.POST.get("otp_code", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if reset_expiry and timezone.now().timestamp() > reset_expiry:
            messages.error(request, _("OTP code has expired. Please request a new code."))
            return render(request, "accounts/verify_forgot_otp.html", {"user_obj": user})

        if otp_input != reset_otp:
            messages.error(request, _("Invalid OTP code. Please enter the correct 6-digit code."))
            return render(request, "accounts/verify_forgot_otp.html", {"user_obj": user})

        if not new_password or len(new_password) < 4:
            messages.error(request, _("Password must be at least 4 characters long."))
            return render(request, "accounts/verify_forgot_otp.html", {"user_obj": user})

        if new_password != confirm_password:
            messages.error(request, _("New password and confirm password do not match."))
            return render(request, "accounts/verify_forgot_otp.html", {"user_obj": user})

        # Update user password
        user.set_password(new_password)
        user.save()

        # Clear reset session variables
        for k in ["reset_user_id", "reset_otp", "reset_expiry"]:
            request.session.pop(k, None)

        AuditLog.objects.create(user=user, action="PASSWORD_RESET", model_name="User", object_id=str(user.id), details=f"User {user.username} reset their password via OTP")
        messages.success(request, _("Password reset successful! Please sign in with your new password."))
        return redirect("/accounts/login/")

    return render(request, "accounts/verify_forgot_otp.html", {"user_obj": user})


def logout_view(request):
    """Sign out committee session."""
    if request.user.is_authenticated:
        AuditLog.objects.create(user=request.user, action="LOGOUT", model_name="User", object_id=str(request.user.id), details=f"User {request.user.username} logged out")
        auth_logout(request)
    messages.info(request, _("You have been logged out."))
    return redirect("/accounts/login/")

