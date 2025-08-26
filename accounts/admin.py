from django.contrib import admin
from .models_folder.user_models import  Profile, Follow
from .models_folder.post_models import  Post, PostMedia, Hashtag, Comment
from .models_folder.notifications_models import  Notification, ActivityLog
from .models_folder.chat_models import  *

# admin.site.register(User)  # Register the User model
admin.site.register(Profile)
admin.site.register(Follow)
admin.site.register(Post)
admin.site.register(PostMedia)
admin.site.register(Hashtag)
admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(ActivityLog)
# admin.site.register(Message)
# admin.site.register(ChatGroup)
# admin.site.register(GroupMessage)
admin.site.register(Message)
admin.site.register(GroupMember)