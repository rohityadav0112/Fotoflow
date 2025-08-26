from django.db import models
from django.contrib.auth.models import User
import re

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("mention", "Mention"),
        ("comment", "Comment"),
        ("reply", "Reply"),
        ("like", "Like"),
        ("follow", "Follow"),
        ("visit", "Profile Visit"),
        ("post_view", "Post View"),              # optional
        ("story_view", "Story View"),            # optional
        ("new_post", "New Post From Following"),
        ("saved_post", "Post Saved"),            # optional
        ("tagged", "Tagged in a Post"),          # optional
        ("shared", "Post Shared"),               # optional
        ("messages", "Messages"),
    ]

    # sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications", null=True, blank=True)
    sender = models.ForeignKey(
    User, 
    on_delete=models.SET_NULL,  # Change this!
    related_name="sent_notifications", 
    null=True, 
    blank=True
)

    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_notifications")  
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, null=True, blank=True)  
    text = models.CharField(max_length=200, default="You have a new notification")
    post = models.ForeignKey("Post", on_delete=models.CASCADE, null=True, blank=True)  
    comment = models.ForeignKey("Comment", on_delete=models.CASCADE, null=True, blank=True)  
    is_read = models.BooleanField(default=False)  
    timestamp = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.notification_type})"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"