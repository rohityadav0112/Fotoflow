from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from accounts.models_folder.chat_models import  Message, Group, GroupMember, GroupJoinRequest
from accounts.forms import *
from accounts.models_folder.notifications_models import  Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def group_chat(request, group_id):
    group = get_object_or_404(Group, id=group_id)

#    SELECT * FROM Message WHERE group_id = group_id AND id NOT IN (SELECT message_id FROM message_deleted_for WHERE user_id = loginuser);
    chats = Message.objects.filter( group_id = group_id).exclude(deleted_for=request.user)
    chats = chats.order_by("timestamp")
    
    return render(request, 'group/group_chat.html',{'group': group, 'chats': chats})

#This will Remain HTTP
@login_required(login_url='login_page')
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
#           SELECT EXISTS (SELECT 1 FROM groupmember WHERE group_id = group_id AND user_id = user_id AND role = 'admin');
    admin = GroupMember.objects.filter(group=group, user=request.user, role='admin').exists()
    owner = True if group.owner == request.user else False
    is_admin = admin or owner

    members = group.memberships.all().exclude(user=group.owner)
    
    join_requests = None
    if is_admin and group.is_private:
        join_requests = GroupJoinRequest.objects.filter(group=group, is_approved=False)
    context = {
        'group': group,
        'members': members,
        'join_requests': join_requests,
        'is_admin': is_admin,
        }
    return render(request, 'group/group_detail.html', context)



#Isme UI Se Message Dikhane Hai 
@login_required(login_url='login_page')
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Already a member?
    if GroupMember.objects.filter(group=group, user=request.user).exists():
        messages.info(request, "You are already a member of this group.")
        return redirect('group_detail', group_id=group.id)
    
    
    if group.is_private:
        # Already sent join request?
        if GroupJoinRequest.objects.filter(group=group, user=request.user).exists():
            messages.info(request, "Join request already sent. Please wait for approval.")
        else:
            GroupJoinRequest.objects.create(group=group, user=request.user)
            messages.success(request, "Join request sent successfully.")

    else:
                # Directly add to group
        GroupMember.objects.create(group=group, user=request.user, role='member')
        messages.success(request, "You have joined the group.")
    print('Error Calling')
    return redirect('groups_list') #This line is giving error
        
#Fixid
@login_required(login_url='login_page')
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    membership = get_object_or_404(GroupMember, group=group, user=request.user)
    owner = True if group.owner == request.user else False
    if group.owner == request.user:
        return HttpResponseForbidden("Group owner cannot leave the group. Transfer ownership first.")
    else:
        membership.delete()
        messages.success(request, "You have left the group successfully.")

    return redirect('groups_list')

# Fixid
@login_required(login_url='login_page')
def add_member(request, group_id):
    group = get_object_or_404(Group, id=group_id)
# Code	Meaning	                                    Example situation
# 401	Unauthorized (not logged in)	            You didn’t log in yet
# 403	Forbidden (logged in, but not allowed)	    You’re logged in, but not an admin
# 404	Not Found	                                The page doesn’t even exist
    admin = GroupMember.objects.filter(group=group, user=request.user, role='admin').exists()
    owner = True if group.owner == request.user else False
    if not admin and not owner:
        return HttpResponseForbidden("Only Admins & Owner can Add.")
    if request.method == 'POST':
        username = request.POST.get('username')
        user = get_object_or_404(User, username=username)

        if GroupMember.objects.filter(group=group, user=user).exists():
            messages.info(request, "User already a member.")
        else:
            GroupMember.objects.create(group=group, user=user, role='member')
            messages.success(request, f"{username} added successfully!")
            
            Notification.objects.create(
                sender = request.user,
                receiver = user,
                text = f'{request.user.username} added You in Group {group.name}: {group.id}'
            )
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "send_notification",
                    "notification":{
                        "type": "",
                        "sender": request.user.username,
                        "text": f"{request.user.username} Added You In Group: {group.name} {group.id}",
                        "timestamp": str(timezone.now())
                    }
                }
            )
        return redirect('group_detail', group_id=group.id)
    return render(request, 'group/add_member.html', {'group': group})


#That is working Fine
@login_required(login_url='login_page')
def promote_member(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    admin = GroupMember.objects.filter(group=group, user=request.user, role='admin').exists()
    owner = True if group.owner == request.user else False
    if not admin and not owner:
        return HttpResponseForbidden("Only Admins & Owner can Promote.")

    membertopromote = get_object_or_404(User, id=user_id)
    if not GroupMember.objects.filter(group=group, user=membertopromote).exists():
        return HttpResponseForbidden("User Does not exist in group.")

    member = get_object_or_404(GroupMember, group=group, user__id=user_id)
    member.role = 'admin'
    member.save()
    messages.success(request, "Promoted to Admin!")
    Notification.objects.create(
        sender = request.user,
        receiver = membertopromote,
        text = f"{request.user} Promot You to 'Admin' For Group: {group.name} : {group.id}"
    )
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{membertopromote.id}",
        {
            "type": "send_notification",
            "notification":{
                "type": "",
                "sender": request.user.username,
                "text": f"{request.user.username} Promot You to 'Admin' For Group: {group.name} : {group.id}",
                "timestamp": str(timezone.now())
            }
        }
    )
    return redirect('group_detail', group_id=group.id)

@login_required(login_url='login_page')
def demote_member(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    
    if not GroupMember.objects.filter(group=group, user=request.user, role='admin').exists():
        return HttpResponseForbidden("Only Admins can promote.")
    
    membertodeomote = get_object_or_404(User, id=user_id)
    if not GroupMember.objects.filter(group=group, user=membertodeomote).exists():
        return HttpResponseForbidden("User Does not exist in group.")
    
    member = get_object_or_404(GroupMember, group=group, user__id=user_id)
    if member.user == group.owner:
        messages.error(request, "Group Owner cannot be demoted!")
    else:
        member.role = 'member'
        member.save()
        messages.success(request, "Demoted to Member.")

    return redirect('group_detail', group_id=group.id)



# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#1
@login_required(login_url='login_page')
def groups_list(request):
    groups = Group.objects.all()

#   Ye query Mujhe vo sari group id de denaga jisme user hai 

#                      select user_id from groupmeber where user=loginuser
    user_memberships = GroupMember.objects.filter(user=request.user).values_list('group_id', flat=True)

#                      select user_id from GroupJoinRequest where user=loginuser
    pending_requests = GroupJoinRequest.objects.filter(user=request.user).values_list('group_id', flat=True)
    # {% if group.id in user_group_ids %}
    return render(request, 'group/group_list.html', {
        'groups': groups,
        'user_group_ids': set(user_memberships),
        "pending_request_ids": pending_requests
    })
    
    
    
    
#It work Perfectly Just thinking to change it to ws
@login_required(login_url='login_page')
def remove_member(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    
    
    admin = GroupMember.objects.filter(group=group, user=request.user, role='admin').exists()
    owner = True if group.owner == request.user else False
    if not owner and not  admin:
        return HttpResponseForbidden("Only Admins & Owner can Promoteee.")
    user = get_object_or_404(User, id=user_id)
    member = get_object_or_404(GroupMember, group=group, user__id=user_id)
    if member.user == group.owner:
        messages.error(request, "Group Owner cannot be demoted!")
    if user == request.user:
        messages.error(request, "You cannot remove themselves!")
    else:
        GroupMember.objects.filter(group=group, user=user).delete()
        messages.success(request, "User removed.")

    return redirect('group_detail', group_id=group.id)

    
    
#It work Perfectly stick to the http because new group should always looks whene we reload
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user  # Step 1: make user the owner
            group.save()
            
            # Step 2: Add the user as an admin in GroupMember
            GroupMember.objects.create(
                group=group,
                user=request.user,
                role=GroupMember.ADMIN
            )

            return redirect('group_detail', group_id=group.id)  # or wherever you wanna go
    else:
        form = GroupForm()
    
    return render(request, 'group/create_group.html', {'form': form})




#This Work Fine, Thinking to apply messages instead of HttpResponses
def cancel_join_request(self, group_id, user_id):
    # Step 1: Check if user is already in group (i.e. request accepted)
    is_exist = GroupMember.objects.filter(user_id=user_id, group_id=group_id).exists()
    if is_exist:
        return HttpResponseForbidden(
            "You can't cancel the request, because your request is already accepted. Reload the page and go to chat."
        )

    # Step 2: Check if the join request exists (means not rejected or not created)
    request = GroupJoinRequest.objects.filter(group_id=group_id, user_id=user_id).first()
    if not request:
        return HttpResponseForbidden(
            'Request Not Found: This Request is Either Already Rejected or Not Created Yet'
        )

    # Step 3: All clear — delete the request
    request.delete()
    return redirect('groups_list')


#ALthough It's workig fie but isme 2-3 chige karni hai
#1: Request Not Found 
#2: user in group --> Request Already Accepted else Already Rejected 
# 3: If he's in group steel accepts buttn will work but do nothing ( I think this can apply everywhere)
@login_required
def accept_join_request(request, group_id, request_id):
    group = get_object_or_404(Group, id=group_id)
    join_request = get_object_or_404(GroupJoinRequest, id=request_id, group=group)
    admin = GroupMember.objects.filter(group_id=group_id, user=request.user, role='admin').exists()
    owner = True if group.owner == request.user else False
    if not admin and not owner:
        return HttpResponseForbidden("Only Admins & Owner can Accept Requests.")

    # Create GroupMember
    GroupMember.objects.create(group=group, user=join_request.user)
    # Delete Request
    join_request.delete()

    Notification.objects.create(
        sender = request.user,
        receiver = join_request.user,
        text = f"{request.user} Accept Your Request To Join  Group: {group.name} : {group.id}"
    )
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{join_request.user_id}",
        {
            "type": "send_notification",
            "notification":{
                "type": "",
                "sender": request.user.username,
                "text": f"{request.user} Accept Your Request To Join  Group: {group.name} : {group.id}",
                "timestamp": str(timezone.now())
            }
        }
    )
    return redirect('group_detail', group_id=group.id)



#ALthough It's workig fie but isme 2-3 chige karni hai
#1: Request Not Found 
#2: user in group --> Request Already Accepted else Already Rejected        
@login_required
def reject_join_request(request, group_id, request_id):
    group = get_object_or_404(Group, id=group_id)
    join_request = get_object_or_404(GroupJoinRequest, id=request_id, group=group)

    # Only Admin can reject
    admin = GroupMember.objects.filter(group_id=group_id, user=request.user, role='admin').exists()
    owner = True if group.owner == request.user else False
    if not admin and not owner:
        return HttpResponseForbidden("Only Admins & Owner can Promote.")

    join_request.delete()

    return redirect('group_detail', group_id=group.id)