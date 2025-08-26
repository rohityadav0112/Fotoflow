from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models_folder.user_models import  Profile, Follow
from accounts.models_folder.post_models import  Post, PostMedia, Hashtag, Comment
from accounts.models_folder.notifications_models import  Notification
from accounts.models_folder.chat_models import  Message, Group, GroupMember


def HomeView(request):
    print('------------------------------------------------------')

    # follower_ids = request.user.followers.values_list('follower', flat=True)
    # followers = User.objects.filter(id__in=follower_ids)

    # for f in followers:
    #     print(f.username)
    #     print('22222222------------------------------------------------------')
    # values_list
    # group_ids = request.user.group_memberships.values_list('group_id', flat=True)
    # group_ids = request.user.group_memberships.values_list('group', flat=True)
    # print('-------------------------------------------------------------------',group_ids)
    # print(group_ids)
    # chats = Message.objects.filter(group__in = request.user.group_memberships).values_list('group', flat=True)

    # print(chats)
#     from your_app.models import GroupMember, Message  # Replace 'your_app' with your actual app name

# # Step 1: Get group IDs where user is a member
# group_ids = GroupMember.objects.filter(user=request.user).values_list('group_id', flat=True)

# # Step 2: Get groups from Message table where group is in those IDs
# chats = Message.objects.filter(group_id__in=group_ids).values_list('group', flat=True).distinct()

    
    posts = Post.objects.all().order_by('-created_at')  # Fetch posts in descending order
    return render(request, 'accounts/home.html', {
        'posts': posts
    })
    
@login_required(login_url='login_page')
def notification(request):
    posts = Post.objects.all().order_by('-created_at')  # Fetch posts in descending order
    return render(request, 'accounts/notification.html')


#Authentication Views
def RegisterView(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        is_private = True if request.POST.get("is_private") else False

        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register_page")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken!")
            return redirect("register_page")

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use!")
            return redirect("register_page")
        

        # If user provides an email, require email verification
        is_active_status = False if email else True

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name, is_active=is_active_status
        )
        user.save()
        Profile.objects.create(user=user, is_private=is_private)

        # If user provided an email, send verification email
        if email:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = request.build_absolute_uri(reverse("verify_email", kwargs={"uidb64": uid, "token": token}))

            send_mail(
                "Verify Your Email - FotoFlow",
                f"Hi {username},\n\nClick the link below to verify your email:\n{verification_link}",
                "piyushyadavji930@gmail.com",
                [email],
                fail_silently=False,
            )

            messages.success(request, "Registration successful! Please check your email for verification.")
        else:
            messages.success(request, "Registration successful! You can now log in.")

        return redirect("login_page")

    return render(request, "authentication/register.html")


def LoginView(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("home_page")  # Redirect to home page (Change if needed)
        else:
            messages.error(request, "Invalid username or password!")

    return render(request, "authentication/login.html")



def VerifyEmailView(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect("login_page")
    else:
        messages.error(request, "Invalid or expired verification link.")
        return redirect("register_page")



def LogoutView(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect("login_page")  # Redirect to login page after logout
