from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
User = get_user_model()

class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE)
    is_private = models.BooleanField(default=False)
    image = models.ImageField(upload_to='group_images/', null=True, blank=True)  # Group Profile Picture
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    MEMBER = 'member'
    ADMIN = 'admin'

    ROLE_CHOICES = (
        (MEMBER, 'Member'),
        (ADMIN, 'Admin'),
    )
    
    group = models.ForeignKey(Group, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='group_memberships', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')  # Prevent duplicate member

    def __str__(self):
        return f"{self.user} in {self.group} as {self.role}"


class GroupJoinRequest(models.Model):
    group = models.ForeignKey(Group, related_name='join_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='sent_group_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user} requested to join {self.group}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages", null=True, blank=True)
    group = models.ForeignKey(Group, related_name="messages", on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField(blank=True, null=True)  # Allow empty messages (for files)
    is_read = models.BooleanField(default=False)  # Track if message is read
    is_deleted = models.BooleanField(default=False)  # Soft delete feature
    deleted_for = models.ManyToManyField(User, related_name="deleted_messages", blank=True)
    likes = models.ManyToManyField(User, related_name="liked_messages", blank=True)  # Like feature
    reply_to = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)  # Reply feature
    timestamp = models.DateTimeField(auto_now_add=True)


    
    class Meta:
            ordering = ['timestamp']

    def __str__(self):
        if self.is_group_message():
            return f"{self.sender} -> Group({self.group.name}): {self.text[:20]}"
        return f"{self.sender} -> {self.receiver}: {self.text[:20]}"

    def clean(self):
        if not self.receiver and not self.group:
            raise ValidationError("Message must have either a receiver (1-to-1) or a group.")

        if self.receiver and self.group:
            raise ValidationError("Message cannot have both receiver and group.")

    def is_group_message(self):
        return self.group is not None