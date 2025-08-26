from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.forms import UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm
from django.contrib import messages
from django.db.models import Count
from django.db.models import Max
# from .models import Post, Comment, PostMedia,Hashtag, Profile, Notification, Follow, Message, Conversation
# from .models import Conversation, Message
from accounts.models_folder.user_models import  Profile, Follow, FollowRequest
from accounts.models_folder.post_models import  Post, PostMedia, Hashtag, Comment
from accounts.models_folder.notifications_models import  Notification
# from accounts.models.chat_models import  Conversation, Message, ChatGroup, GroupMessage
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from accounts.system_notifications.notification import notification_db

@login_required(login_url='login_page')
def SearchUserProfile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    is_owner = request.user == user
    is_follower = Follow.objects.filter(follower=request.user, following=user).exists()
    is_private = profile.is_private
    follow_request_sent = FollowRequest.objects.filter(owner=user, request=request.user).exists()

    # Show posts only if:
    # - profile is public
    # - OR request.user is owner
    # - OR request.user is a follower
    show_posts = not is_private or is_owner or is_follower

    posts = Post.objects.filter(user=user).order_by('-created_at') if show_posts else []
    # print(f'{request.user.username} is entering {user.username}')
    notification_db(sender=request.user,
        receiver=user,
        type="visit",
    )
    context = {
        'user': user,
        'profile': profile,
        'posts': posts,
        'followers_count': Follow.objects.filter(following=user).count(),
        'following_count': Follow.objects.filter(follower=user).count(),
        'is_following': is_follower,
        'is_owner': is_owner,
        'is_private': is_private,
        'follow_request_sent': follow_request_sent,
        'show_posts': show_posts,
    }

    return render(request, "accounts/search_user_profile.html", context)


@login_required(login_url='login_page')
def ProfileView(request):
    profile = get_object_or_404(Profile, user=request.user)
    posts = Post.objects.filter(user=request.user).order_by('-created_at')  # Get user's posts in descending order
    is_liked = request.user in posts
    followers_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()
    variables = {
        "profile": profile,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
    }
    return render(request, 'accounts/profile.html', variables)


# DOne
@login_required(login_url='login_page')
def ProfileUpdateView(request):
    user = request.user
    profile = request.user.profile  # Get the logged-in user's profile

    if request.method == "POST":

        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()
            
            
            messages.success(request, 'Profile Updated Succefully')
            return redirect("profile_update_page")  # Redirect to profile update page after saving
        else:
            pass #Don't need to weite anything here

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, "accounts/profile_update.html", {"user_form": user_form, "profile_form": profile_form})






@login_required(login_url='login_page')
def FollowUnfollowView(request, username):
    print('FollowUnfollowView Is calling')
    user_to_follow = get_object_or_404(User, username=username)
    if request.user == user_to_follow:
        messages.error(request, "You can't follow yourself!")
        return redirect('myprofile_page', username=username)
    
    follow_relation, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)

    if not created:  
        follow_relation.delete()
        messages.success(request, f"You unfollowed {user_to_follow.username}")
    else:
        messages.success(request, f"You followed {user_to_follow.username}")
        
        Notification.objects.create(
            sender = request.user,
            receiver = user_to_follow,
            notification_type = "follow",
            text = f"{request.user.username} Started Following You",
            
        )
        
        channel_layer = get_channel_layer() #Isme question hai ki ye aise kyu likha hai why na direct get_cha_layer karke jaise consumers me karte hai 
        async_to_sync(channel_layer.group_send)(
            f"user_{user_to_follow.id}",
            {
                "type": "send_notification",
                "notification":{
                    "type": "follow",
                    "sender" : request.user.username,
                    "text": f'{request.user.username} started Following You',
                    "timestamp": str(timezone.now())
                }
            }
        )
        

    return redirect('search_profile_page', username=username)



@login_required(login_url='login_page')
def FollowerListView(request, username):
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')

    return render(request, 'accounts/followers_list.html', {'user': user, 'followers': followers})

@login_required(login_url='login_page')
def FollowingListView(request, username):
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')

    return render(request, 'accounts/following_list.html', {'user': user, 'following': following})


@login_required(login_url='login_page')
def send_follow_request(request, username):
    print('send_follow_request Is calling')
    
    owner = get_object_or_404(User, username=username)

    if owner == request.user:
        messages.error(request, "You can't send request to yourself!")
        return redirect('search_profile_page', username=username)

    follow_request, created = FollowRequest.objects.get_or_create(owner=owner, request=request.user)

    if not created:
        follow_request.delete()
        messages.success(request, "Follow request cancelled.")
    else:
        messages.success(request, "Follow request sent.")
        Notification.objects.create(
            sender=request.user,
            receiver=owner,
            notification_type="follow request",
            text=f"{request.user.username} has sent you a follow request"
        )

        # print(f'{request.user.username} is sendint {user.username}')
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{owner.id}",  # Each user in their own group
            {
                "type": "send_notification",
                "notification": {
                    "type": "visit",
                    "sender": request.user.username,
                    "text": f"{request.user.username} has sent you a follow request",
                    "timestamp": str(timezone.now())
                }
            }
        )
        

    return redirect('search_profile_page', username=username)
    
    
@login_required(login_url='login_page')
def follow_request_accept(request, req_id):
    follow_request = get_object_or_404(FollowRequest, id=req_id, owner=request.user, is_accepted=False)

    # request is the user who sent the request
    follower_user = follow_request.request
    following_user = follow_request.owner  # this is owner

    # Create the follow relationship
    Follow.objects.create(
        follower=follower_user,
        following=following_user
    )

    follow_request.delete()
    Notification.objects.create(
            sender=request.user,
            receiver=follower_user,
            notification_type="follow request",
            text=f"{request.user.username} has accepted  your  follow request"
        )

        # print(f'{request.user.username} is sendint {user.username}')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{follower_user.id}",  # Each user in their own group
        {
            "type": "send_notification",
            "notification": {
                "type": "follow request",
                "sender": request.user.username,
                "text": f"{request.user.username} has accepted  your  follow request",
                "timestamp": str(timezone.now())
            }
        }
    )
    messages.success(request, f'{follower_user.username} is now your follower!')
    return redirect('follow_request_list')

        
@login_required(login_url='login_page')
def follow_request_reject(request, req_id):
    follow_request = get_object_or_404(FollowRequest, id=req_id, owner=request.user, is_accepted=False)

    rejected_user = follow_request.request
    follow_request.delete()

    messages.success(request, f'{rejected_user.username}\'s follow request has been rejected.')
    return redirect('follow_request_list')

        
    # print('follow_request_accept Is calling')
    # owner = get_object_or_404(User, username=request.user)

    # if not owner:
    #     messages.error(request, "Only Owner Can Accept Or Reject Requests!")
    #     return redirect('profile_page')

    # follow_request, created = FollowRequest.objects.get_or_create(owner=owner, request=request.user)

    # if not created:
    #     follow_request.delete()
    #     messages.success(request, "Follow request cancelled.")
    # else:
    #     messages.success(request, "Follow request sent.")

    # return redirect('follow_request_list',)


@login_required(login_url='login_page')
def follow_request_list(request):
    # Get all unaccepted requests sent TO the logged-in user
    pending_requests = FollowRequest.objects.filter(owner=request.user, is_accepted=False)

    return render(request, 'accounts/follow_request_list.html', {
        'pending_requests': pending_requests
    })
    
    
    
    