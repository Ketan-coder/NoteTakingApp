from datetime import datetime
import email
import uuid
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from Notes.models import Activity
from Timely.Notes.utils import send_email

from .forms import ProfileForm, UserRegistrationForm
from .models import Profile

# Create your views here.

@login_required
def updateUser(request):
    user = request.user

    # Ensure email is verified before allowing profile update
    if not user.is_active:
        messages.error(request, "You must verify your email before updating your profile.")
        return redirect("email_confirmation_pending")

    profile = Profile.objects.get(user=user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        bio = request.POST.get("bio", "").strip()

        # ✅ Basic Validation
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "❌ Username is already taken.")
            return redirect("update_user")

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "❌ Email is already in use.")
            return redirect("update_user")

        # ✅ Save Updates
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        profile.bio = bio
        profile.firstName = first_name
        profile.lastName = last_name
        profile.email = email
        profile.save()

        # ✅ Log Activity
        Activity.objects.create(
            author=user, title="Updated Profile", body="Updated Profile"
        )

        messages.success(request, "Profile updated successfully")
        return redirect("home")

    context = {"user": user, "profile": profile}
    return render(request, "user_update.html", context)

def login_form(request):
    context = {"title": "Login"}
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful")
            send_email(
                to_email=user.email,
                subject="Login Alert",
                title="Login Alert Notification",
                body=f"Your account with username '{user.username}' was accessed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. If this was not you, please reset your password to secure your account!.",
                anchor_link="https://codingfox.pythonanywhere.com/users/password-reset/",
                anchor_text="Reset Password"
            )
            # subject, from_email, to = (
            #     "Login Alert",
            #     "codingfoxblogs@gmail.com",
            #     f"{user.email}",
            # )
            # text_content = "This is an important message."
            # html_content = f'<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">\n<head><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200&display=swap" rel="stylesheet">\n<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting"><title></title></head<body style="margin:0;padding:0;font-family:"Poppins",Arial,sans-serif;"><table role="presentation" style="width:100%;border-collapse:collapse;border:0;border-spacing:0;background:#ffffff;"><tr><td align="center" style="padding:0;"><table role="presentation" style="width:602px;border-collapse:collapse;border:1px solid #cccccc;border-spacing:0;text-align:left;"><tr><td align="center" style="padding:40px 0 30px 0;background:#efefef;"><h1>Timely</h1></td></tr><tr><td style="padding:36px 30px 42px 30px;"><table role="presentation" style="width:100%;border-collapse:collapse;border:0;border-spacing:0;"><tr><td style="padding:0 0 36px 0;color:#153643;"><h1 style="font-size:24px;margin:0 0 20px 0;font-family:Arial,sans-serif;">Login Alert Mail</h1><p style="margin:0 0 12px 0;font-size:16px;line-height:24px;font-family:Arial,sans-serif;">This is to tell you that your account with username: {username} signing in at {datetime.now()}, If this is not you please consider changing your password immediately!</p><h3 style="margin:0;line-height:24px;font-family:Arial,sans-serif;"><a href="https://codingfox.pythonanywhere.com/users/password-reset/" style="padding: 1%; background-color: #0076d1; color: white;text-decoration: none;">Reset Password!</a></h3><br><p>Please do not reply to this email address, Mail me here: <a href="mailto:ketanv288@gmail.com" style="background-color: transparent; color: #0076d1;text-decoration: none;">Mail Me!</a></p></td></tr></table></body></html>'
            # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            # msg.attach_alternative(html_content, "text/html")
            # msg.send()
            return redirect("home")
        else:
            messages.error(request, f"Account Does Not Exists with {username}")
            return render(request, "login.html", context)
    return render(request, "login.html", context)


def logout_form(request):
    context = {"title": "Logout"}
    logout(request)
    return render(request, "logout.html", context)


def registeration_form(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            messages.success(request, f"Account created for {username}! Just Login")
            # messages.warning(request,f'Upon Regiestering you are agreeing with the using required cookies')
            # subject, from_email, to = f'Welcome {username}', 'codingfoxblogs@gmail.com', f'{email}'
            # text_content = 'This is an important message.'
            # html_content = (f'<div style="background-color: hsl(206, 98%, 90%);color: #363636;width: 90%;height: auto;font-weight: 300;padding: 5%;"><h1 style="text-align:center;">Welcome {username}!</h1><br><h3> Explore the website CodingFox Blogs, you can also create Blogs on this blog page at no cost<br><a href="https://codingfox.pythonanywhere.com/" style="padding: 1%; background-color: #0076d1; color: white;text-decoration: none;">Explore More!</a></h3><br><p>Please do not reply to this gmail, if you want to contact mail here for any query <a href="mailto:ketanv288@gmail.com">📧Mail Me</a></p></div>')
            # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            # msg.attach_alternative(html_content, "text/html")
            # msg.send()
            return redirect("login")
    else:
        form = UserRegistrationForm()
    context = {"title": "Register", "form": form}
    return render(request, "newuser.html", context)



def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html", {"title": "Register"})

        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            messages.error(request, "Email is already registered. Try logging in.")
            return render(request, "register.html", {"title": "Register"})

        # ✅ Step 1: Create User First
        user = User.objects.create_user(username=email, email=email, password=password)
        user.is_active = False  # User is inactive until email confirmation
        user.save()

        profile = Profile.objects.get(user=user)
        profile.email_confirmation_token = uuid.uuid4()
        profile.save()

        # ✅ Step 4: Send Confirmation Email
        confirmation_link = f"{settings.SITE_URL}/accounts/confirm-email/{profile.email_confirmation_token}/"
        send_email(
            to_email=user.email,
            subject="Confirm Your Timely Account",
            title="Complete Your Registration",
            body="Thank you for registering! Please confirm your email by clicking the button below.",
            anchor_link=confirmation_link,
            anchor_text="Confirm Email"
        )
        print(confirmation_link)
        # subject = "Confirm Your Timely Account"
        # from_email = "codingfoxblogs@gmail.com"
        # to = user.email
        # text_content = "Please confirm your email."
        # html_content = f'''
        # <html lang="en">
        # <head>
        #     <meta charset="UTF-8">
        #     <meta name="viewport" content="width=device-width, initial-scale=1">
        #     <title>Email Confirmation</title>
        # </head>
        # <body style="font-family: 'Poppins', Arial, sans-serif; background: #ffffff; padding: 20px;">
        #     <h2 style="color: #0076d1;">Confirm Your Email for Timely</h2>
        #     <p>Hello,</p>
        #     <p>Thank you for registering with Timely. Please click the link below to confirm your email address:</p>
        #     <p><a href="{confirmation_link}" style="padding: 10px; background-color: #0076d1; color: white; text-decoration: none;">Confirm Email</a></p>
        #     <p>If you did not sign up, please ignore this email.</p>
        # </body>
        # </html>
        # '''
        # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        # msg.attach_alternative(html_content, "text/html")
        # msg.send()

        messages.success(request, "Registration successful. Check your email to confirm your account.")
        return redirect("email_confirmation_pending")  # ✅ Fixed the URL name

    return render(request, "register.html", {"title": "Register"})


def email_confirmation_view(request, token):

    try:
        token_uuid = uuid.UUID(token)  # ✅ Convert token from str to UUID
    except ValueError:
        raise Http404("Invalid Token Format")  # If the token is not a valid UUID

    try:
        profile = Profile.objects.get(email_confirmation_token=token_uuid)  # ✅ Query with UUID
    except Profile.DoesNotExist:
        raise Http404("Invalid or Expired Token")  

    # Activate user and remove token
    profile.user.is_active = True
    profile.user.save()
    profile.email_confirmation_token = None  # Remove token after activation
    profile.save()

    login(request, profile.user)
    messages.success(request, "Email confirmed! Complete your profile.")
    return redirect("profile_setup")


def profile_setup_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        bio = request.POST.get("bio")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "profile_setup.html", {"title": "Complete Profile"})

        user = request.user
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        Profile.objects.filter(user=user).update(bio=bio, firstName=first_name, lastName=last_name, email=user.email)

        messages.success(request, "Profile updated successfully.")
        return redirect("home")

    return render(request, "profile_setup.html", {"title": "Complete Profile"})

def check_username(request):
    username = request.GET.get("username", "").strip()
    
    if not username:
        return HttpResponse('<span style="color: red;">❌ Username cannot be empty</span>')

    if User.objects.filter(username=username).exists():
        return HttpResponse('<span style="color: red;">❌ Username is already taken</span>')
    
    return HttpResponse('<span style="color: green;">✅ Username is available</span>')


@login_required
def update_email_request(request):
    if request.method == "POST":
        new_email = request.POST.get("new_email").strip()

        if User.objects.filter(email=new_email).exists():
            messages.error(request, "❌ This email is already in use.")
            return redirect("update_user")

        # Generate verification token
        profile = request.user.profile
        profile.email_confirmation_token = uuid.uuid4()
        profile.save()

        # Send email verification link
        confirmation_link = f"{settings.SITE_URL}/confirm-new-email/{profile.email_confirmation_token}/{new_email}/"
        subject = "Confirm Your New Email"
        from_email = "codingfoxblogs@gmail.com"
        to = new_email
        text_content = "Please confirm your new email."
        html_content = f'''
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Email Confirmation</title>
        </head>
        <body style="font-family: 'Poppins', Arial, sans-serif; background: #ffffff; padding: 20px;">
            <h2 style="color: #0076d1;">Confirm Your New Email</h2>
            <p>Hello,</p>
            <p>Click the link below to verify and update your email address:</p>
            <p><a href="{confirmation_link}" style="padding: 10px; background-color: #0076d1; color: white; text-decoration: none;">Confirm New Email</a></p>
            <p>If you did not request this change, please ignore this email.</p>
        </body>
        </html>
        '''
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(request, "Verification email sent. Please check your new email.")
        return redirect("update_user")

    return redirect("update_user")

@login_required
def confirm_new_email(request, token, new_email):
    profile = get_object_or_404(Profile, email_confirmation_token=token)

    # Ensure the logged-in user is updating their email
    if profile.user != request.user:
        messages.error(request, "❌ Unauthorized request.")
        return redirect("home")

    # Update email and clear token
    profile.user.email = new_email
    profile.user.save()
    profile.email = new_email
    profile.email_confirmation_token = None
    profile.save()

    messages.success(request, "✅ Your email has been updated successfully!")
    return redirect("update_user")