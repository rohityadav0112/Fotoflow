from accounts.models_folder.notifications_models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.utils import timezone


def notification_db(receiver=None, sender=None, type=None, text=None):
    
    print('notificationnnnnnnnnnnn eroooooooooooor')
    if type:
        if type == "mention": 
            text = f"@{sender.username} mentioned you in a post.",
            ws_text = f"🔔 @{sender.username} mentioned you in a post! 🗣️",
        elif type == "comment": 
            text = f"@{sender.username} commented on your post.",
            ws_text =  f"💬 @{sender.username} commented on your post! 📝",
        elif type == "reply":
            text =  f"@{sender.username} replied to your comment.",
            ws_text = f"↩️ @{sender.username} replied to your comment! 💭",
        elif type == "like":
            text =  f"@{sender.username} liked your post.",
            ws_text = f"❤️ @{sender.username} liked your post! 👍",
        elif type == "follow":
            text =  f"@{sender.username} started following you.",
            ws_text =  f"👤 @{sender.username} started following you! 🚶‍♂️",
        elif type == "visit":
            text =  f"@{sender.username} visited your profile.",
            ws_text = f"👀 @{sender.username} checked out your profile! 🧭",
        elif type == "post_view":
            text =  f"@{sender.username} viewed your post.",
            ws_text = f"👁️ @{sender.username} viewed your post! 🖼️",
        elif type == "story_view":
            text =  f"@{sender.username} viewed your story.",
            ws_text = f"🎥 @{sender.username} viewed your story! ⏳",
        elif type == "new_post":
            text = f" @{sender.username} just shared a new post! Check it out ", 
            ws_text = f"🆕 @{sender.username} just shared a new post! Check it out 📸",
            #  "new_post": "🆕 {sender} just shared a new post! Check it out 📸", 
        elif type == "saved_post":
            text =  f"@{sender.username} saved your post.",
            ws_text = f"💾 @{sender.username} saved your post! 🔖",
        elif type == "tagged":
            text =  f"@{sender.username} tagged you in a post.",
            ws_text = f"🏷️ @{sender.username} tagged you in a post! 📌",
        elif type == "shared":
            text =  f"@{sender.username} shared your post.",
            ws_text = f"🔗 @{sender.username} shared your post! 📤",
        elif type == "messages":
            text =  f"You have a new message from {sender.username}.",
            ws_text =  f"👤 @{sender.username} started following you! 🚶‍♂️",
    else:
        text =  f"You have a new notification!",
        ws_text =  f"🔔 You have a new notification! ✨",
        
        
    Notification.objects.create(
        sender=sender,
        receiver=receiver,
        notification_type=type,
        text=text
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{receiver.id}",  # Each user in their own group
        {
            "type": "send_notification",
            "notification": {
                "type": "visit",
                "sender": sender.username if sender else None,
                "text": ws_text,
                "timestamp": str(timezone.now())
            }
        }
    )
