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
from django.db.models import Count
from django.db.models import Max
# from .models import Post, Comment, PostMedia,Hashtag, Profile, Notification, Follow, Message, Conversation
# from .models import Conversation, Message
from accounts.models_folder.user_models import  Profile, Follow
from accounts.models_folder.post_models import  Post, PostMedia, Hashtag, Comment
from accounts.models_folder.notifications_models import  Notification
# from accounts.models.chat_models import  Conversation, Message, ChatGroup, GroupMessage



# @login_required(login_url='login_page')
# def NotificationsView(request):
#     # get notification which are unread 
#     notifications = Notification.objects.filter(receiver=request.user, is_read=False).order_by('-timestamp')
    

#     # print("Notifications:", notifications)  
#     # Mark notifications as read
#     notifications.update(is_read=True)

#     return render(request, 'accounts/notifications.html', {'notifications': notifications})



# @login_required(login_url='login_page')
# def NotificationReadView(request):
#     if request.method == "POST":
#         request.user.notifications.filter(is_read=False).update(is_read=True)
#     return redirect("notifications_page")


def SearchUserView(request):
    query = request.GET.get("q")  # Get search query from URL
    results = []

    if query:
        results = User.objects.filter(username__startswith=query) | User.objects.filter(email__icontains=query)

    return render(request, "accounts/search.html", {"results": results, "query": query})
