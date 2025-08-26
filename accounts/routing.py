from django.urls import re_path
# from accounts.consumer_files.chats_consumers import ChatConsumer, GroupChatConsumer
from .consumers import ChatConsumer, GroupChatConsumer, PostConsumer, NotificationConsumer


websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/groupchat/(?P<group_id>\d+)/$", GroupChatConsumer.as_asgi()),
    # re_path(r'ws/post/(?P<post_id>\d+)/$', PostConsumer.as_asgi()),
    re_path(r'ws/post/(?P<post_id>\d+)/$', PostConsumer.as_asgi()),
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]