import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from accounts.models_folder.post_models import Post, PostMedia
from accounts.models_folder.notifications_models import ActivityLog #need to create here
from django.contrib.auth import get_user_model
User = get_user_model()
import re
from accounts.system_notifications.notification import notification_db

# === Config ===
QUEUE_MAX_SIZE = 5

# === The task queue ===
post_request_queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)



# === Function to enqueue a request ===
# isko user call kar raha hai with parameter
def enqueue_post_task(user, caption, post):
    post_request_queue.put((user, caption, post))


# === Worker Thread Target ===
def worker_fu():
    while True:
        user, caption, post = post_request_queue.get()

        # For this request, we run 3 tasks concurrently
        with ThreadPoolExecutor(max_workers=3) as task_executor:
            task_executor.submit(notify_mentions, user, caption)
            task_executor.submit(notify_followers, user)  # Placeholder
            task_executor.submit(log_activity, user)

        post_request_queue.task_done()




# Task To Be Perfoms


# Now it shifted to views
def save_post_and_media(user, caption, media_files):
    print(f"[{user.username}] ⏳ Saving post and media to DB...")
    from accounts.models_folder.post_models import Post, PostMedia


    post = Post.objects.create(user=user, caption=caption)
    print('post owner', post.user.username)

    for file in media_files:
        print('Savin Post')
        PostMedia.objects.create(post=post, file=file)
    print(f"[{user.username}] ✅ Post saved!")


def notify_mentions(post_owner, caption):
    print("Mention Is calling")
    mentionusers =  re.findall(r'@(\w+)', caption)
    
    for mentionuser in mentionusers:
        mentionuser_obj = User.objects.get(username=mentionuser)
        notification_db(sender=post_owner,
            receiver=mentionuser_obj,
            type="mention",
        )
        
        
# === Subtask: Log activity ===
def log_activity(user):
    print('log_activity for post')
    print(f"[{user.username}] 📝 Logging activity...")
    ActivityLog.objects.create(
        user=user,
        action="created a post",
        timestamp=timezone.now()
    )
    
def notify_followers(post_owner):
    
    follower_ids = post_owner.followers.values_list('follower', flat=True)
    followers = User.objects.filter(id__in=follower_ids)


    for follower in followers:
        follower_obj = User.objects.get(username=follower)
        notification_db(sender=post_owner,
            receiver=follower_obj,
            type="new_post",
        )

