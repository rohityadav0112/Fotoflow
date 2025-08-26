from accounts.models_folder.chat_models import Message
from accounts.models_folder.notifications_models import Notification
from accounts.models_folder.user_models import Profile
from django.db.models import Q
from apscheduler.schedulers.background import BackgroundScheduler
from django.contrib.auth import get_user_model
import time
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from datetime import date


User = get_user_model()
scheduler = BackgroundScheduler()

def count_unread_messages():
    for user in User.objects.filter(is_active=True):
        group_ids = user.group_memberships.values_list('group', flat=True)
        messages = Message.objects.filter(
            Q(receiver=user) | Q(group_id__in=group_ids),
            is_deleted=False,
            is_read=False
        )
        if messages.exists():
            Notification.objects.create(
                receiver=user,
                notification_type="messages",
                text=f"You have  {messages.count()} unread messages."
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",  # Each user in their own group
                {
                    "type": "send_notification",
                    "notification": {
                        "type": "messages",
                        "text": f"🔔 You have  {messages.count()} unread messages.",
                        "timestamp": str(timezone.now()),
                        "sender": None 
                    }
                }
            )

def birth_day_wish():
    for user in User.objects.filter(is_active=True):
        today = date.today()
        birthday_profiles = Profile.objects.filter(dob__month=today.month, dob__day=today.day)
        if birthday_profiles:
            for profile in birthday_profiles:
                Notification.objects.create(
                    receiver=profile.user,
                    notification_type="messages",
                    text=f"Happy Birthday, {profile.user.username}!"
                )

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{profile.user.id}",  # Each user in their own group
                    {
                        "type": "send_notification",
                        "notification": {
                            "type": "messages",
                            "text": f"🎂 Happy Birthday, {profile.user.username}!",
                            "timestamp": str(timezone.now()),
                            "sender": None 
                        }
                    }
                )
        
def anniversary_feedback():
    today = date.today()
    anniversary_users = User.objects.filter(
        date_joined__month=today.month,
        date_joined__day=today.day,
        is_active=True
    )

    for user in anniversary_users:
        years = today.year - user.date_joined.year
        if years >= 1:
            Notification.objects.create(
                receiver=user,
                notification_type="messages",
                text=f"Congrats {user.username}, on completing {years} year(s) on FotoFlow!"
                # text=f"🎉 Congrats {user.username}, you've completed {years} year(s) on FotoFlow! We'd love your feedback! 💬"
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",  # Each user in their own group
                {
                    "type": "send_notification",
                    "notification": {
                        "type": "messages",
                        "text":f"🎉 Congrats {user.username}, you've completed {years} year(s) on FotoFlow! We'd love your feedback! 💬",
                        "timestamp": str(timezone.now()),
                        "sender": None 
                    }
                }
            )

            # print(f"🎉 Congrats {user.username}, you've completed {years} year(s) on FotoFlow! We'd love your feedback! 💬")
    
def start_scheduler():
    scheduler.add_job(count_unread_messages, 'cron', hour=20, minute=0) #every day at 8PM
    scheduler.add_job(birth_day_wish, 'cron', hour=8, minute=0) #wish birthday at morning 8AM
    scheduler.add_job(anniversary_feedback, 'cron', hour=8, minute=0) 

    scheduler.start()