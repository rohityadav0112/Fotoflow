from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models import Max
from accounts.models_folder.user_models import  Profile, Follow
from accounts.models_folder.chat_models import  Message
from django.db.models import Q

@login_required(login_url='login_page')
def chat_view(request, username):
    other_user = get_object_or_404(User, username=username)
    room_name = get_roomname(other_user, request.user)
    print(f"Views(cv)-->RoomName: {room_name}")
    chats = Message.objects.filter(
        receiver__in = [other_user, request.user],
        sender__in = [other_user, request.user],
    ).exclude(deleted_for=request.user)
    chats = chats.order_by("timestamp")

    return render(request, 'chats/chat.html', {"chats": chats, "room_name": room_name, "other_user": other_user})

def get_roomname(user1, user2):
    usernames = sorted([user1.username, user2.username])
    print(f"Views(gr)-->RoomName: chat_{usernames[0]}_{usernames[1]}")
    return f"chat_{usernames[0]}_{usernames[1]}"
    
    
@login_required(login_url='login_page')
def inbox_view(request):
    group_ids = request.user.group_memberships.values_list('group', flat=True)
    chats = Message.objects.filter(Q(sender = request.user) | Q(receiver = request.user) | Q(group_id__in = group_ids))
    
    return render(request, 'chats/inbox.html', {"chats" : chats})
#     sender
# receiver
# group












# @login_required(login_url='login_page')
# def chat_view(request, username):
#     other_user = get_object_or_404(User, username=username)
#     room_name = get_roomname(other_user, request.user)
#     print(f"Views(cv)-->RoomName: {room_name}")
#     chats = Message.objects.filter(
#         receiver__in = [other_user, request.user],
#         sender__in = [other_user, request.user],
#     ).exclude(deleted_for=request.user)
#     chats = chats.order_by("timestamp")

#     return render(request, 'chats/chat.html', {"chats": chats, "room_name": room_name, "other_user": other_user})

# def get_roomname(user1, user2):
#     usernames = sorted([user1.username, user2.username])
#     print(f"Views(gr)-->RoomName: chat_{usernames[0]}_{usernames[1]}")
#     return f"chat_{usernames[0]}_{usernames[1]}"