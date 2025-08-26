from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync, sync_to_async
from .models import Message, Group
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils import timezone
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models_folder.chat_models import (
    Group,
    Message,
    GroupMember,
    GroupJoinRequest,
)
from .models_folder.post_models import (
    Post,
    Comment,
)
from .models_folder.notifications_models import (
    Notification
)
User = get_user_model()



# Consumers Start

class NotificationConsumer(AsyncWebsocketConsumer):
    print("Notificatin Accept")
    async def connect(self):
        self.user = self.scope["user"]
        self.group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        print(f"Notificatin Group : {self.group_name}")
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"Notificatin Group : {self.group_name} Discon" )


    # print(f"Notificatin Group : {self.group_name} Discon" )
    async def send_notification(self, event):
        notification = event["notification"]
        sender = notification.get("sender")

        if sender:
            # sender exists, send sender info as is (assuming it's a string or something simple)
            sender_data = sender
        else:
            # no sender, send "System" or None
            sender_data = "System"

        await self.send(text_data=json.dumps({
            "type": notification.get("type"),
            "sender": sender_data,
            "text": notification.get("text"),
            "timestamp": notification.get("timestamp"),
        }))

# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------
class PostConsumer(AsyncWebsocketConsumer):


    async def connect(self):
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'post_{self.post_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action_type = data.get("type")
        print('Message Receving')
        if action_type == "toggle_like":
            print('For Like')
            await self.handle_toggle_like(data)
        elif action_type == "new_comment":
            print('For  Comment')
            await self.handle_new_comment(data)
        elif action_type == "new_reply":
            print('For Rep Comment')
            await self.handle_new_reply(data)

    async def handle_toggle_like(self, data):
        print('Enter To Like Handle')
        # post = await sync_to_async(Post.objects.get)(id=self.post_id)
        post = await database_sync_to_async(Post.objects.get)(id=self.post_id)
        user = self.scope['user']

        is_liked = data["is_liked"]
        
        if is_liked:
            await sync_to_async(post.likes.remove)(user)
            print('Enter To UnLike')
            liked = False
        else:
            await sync_to_async(post.likes.add)(user)
            liked = True
            
            print('Enter To Like')
            post_user = await sync_to_async(lambda: post.user)()
            if post_user != user:
                await self.create_like_notification(sender=user, receiver=post_user, post=post)
            

        total_likes = await sync_to_async(post.total_likes)()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "like_update_broadcast",
                "total_likes": total_likes
            }
        )
        print('Enter To Like Group Layer')

        # 2. Send is_liked only to the user who clicked (this user)
        await self.send(text_data=json.dumps({
            "type": "like_update_personal",
            "is_liked": liked
        }))
        print('Enter To Like Icon Change')
                
                
    async def like_update_broadcast(self, event):
        print('Enter To Like Count Brodcast')
        print('-------------------------------------------------------------------')
        print('-------------------------------------------------------------------')
        print('-------------------------------------------------------------------')
        print('-------------------------------------------------------------------')
        await self.send(text_data=json.dumps({
            "type": "like_update_broadcast",
            "total_likes": event["total_likes"]
        }))
        
    @database_sync_to_async
    def create_like_notification(self, sender, receiver, post):
        Notification.objects.create(
            sender=sender,
            receiver=receiver,
            notification_type="like",
            text=f"{sender.username} liked your post.",
            post=post
        )
        async_to_sync(self.channel_layer.group_send)(
            f"user_{receiver.id}",
            {
                "type": "send_notification",
                "notification": {
                    "type": "like",
                    "sender": sender.username,
                    "text": f"{sender.username} liked your post.",
                    "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        )
        
    async def handle_new_comment(self, data):
        user = await sync_to_async(User.objects.get)(username=data["username"])
        post = await sync_to_async(Post.objects.get)(id=self.post_id)
        comment = await sync_to_async(Comment.objects.create)(
            post=post, user=user, text=data["text"]
        )
        
        comment_text = data["text"] #This will send to the notification
        post_user = await sync_to_async(lambda: post.user)()
        if post_user != user:
            # print("StartCommnetNotification")
            await self.create_comment_notification(sender=user, receiver=post_user,  post=post, comment_text=comment_text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "new_comment",
                "comment": {
                    "id": comment.id,
                    "username": user.username,
                    "text": comment.text
                }
            }
        )

    @database_sync_to_async
    def create_comment_notification(self, sender, receiver, post, comment_text):
        Notification.objects.create(
            sender=sender,
            receiver=receiver,
            notification_type = "comment",
            text=f"{sender.username} comment on you post :{comment_text}",
            # text=f"{sender.username} comment your post.",
            
            post=post
        )
        
        async_to_sync(self.channel_layer.group_send)(
            f"user_{receiver.id}",
            {
                "type": "send_notification",
                "notification":{
                    "type": "comment",
                    "sender": sender.username,
                    "text": f"{sender.username} comment on  your post: {comment_text}",
                    "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                }
            }
        )
        
    async def handle_new_reply(self, data):
        user = await sync_to_async(User.objects.get)(username=data["username"])
        post = await sync_to_async(Post.objects.get)(id=self.post_id)
        parent = await sync_to_async(Comment.objects.get)(id=data["parent_id"])
        reply = await sync_to_async(Comment.objects.create)(
            post=post, user=user, text=data["text"], parent=parent
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "new_reply",
                "reply": {
                    "id": reply.id,
                    "parent_id": parent.id,
                    "username": user.username,
                    "text": reply.text
                }
            }
        )

    # Handlers to send data to frontend


    async def new_comment(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_comment",
            "comment": event["comment"]
        }))

    async def new_reply(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_reply",
            "reply": event["reply"]
        }))


# -----------------------------------------------------------------------------------------------------------------------------------------------------------
class GroupChatConsumer(AsyncWebsocketConsumer):











    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f"group_chat_{self.group_id}"  # Channel Layer Group Name
        print('GroupChatConsumer', self.group_name)
        # Add to group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # This will handle incoming WebSocket messages
        data = json.loads(text_data)
        sender = self.scope['user']
        text = data.get("text", "").strip()
        action = data.get("action", None)
        reply_to_id = data.get("reply_to", None)
        message_id = data.get("message_id", None)
        
        if action == "delete":
            delete_type = data.get("delete_type")
            messageid = data.get("message_id")
            print('DelelteMessagesId', messageid)
            await self.delete_message(message_id, sender, delete_type)
            return
        
        if action == "like":
            await self.like_message(message_id, sender)
            return

        # Save to DB
        msg = await self.save_message(sender, text, reply_to_id)

        # Send message to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                "id": msg.id,
                "text": text,
                "sender":sender.username,
                "reply_to": reply_to_id
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "text": event["text"],
            "sender": event["sender"],
            "reply_to": event["reply_to"],
        }))


    @database_sync_to_async
    def save_message(self, sender, text, reply_to_id):
        print('GroupChatConsumer, Message Saving: ', text)
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id)
            except Message.DoesNotExist:
                pass
        group = Group.objects.get(id=self.group_id)
        return Message.objects.create(
            sender=sender,
            group=group,
            text=text,
            reply_to=reply_to
        )
        #
    async def delete_message(self, msg_id, user, delete_type):
        print("Delete Message Calling")
        try:
            msg = await sync_to_async(Message.objects.select_related("sender").get)(id=msg_id)
            if delete_type == "everyone":
                if msg.sender_id == user.id:
                    msg.is_deleted = True
                    await sync_to_async(msg.save, thread_sensitive=True)()
                    
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "delete_message_event",
                            "message_id": msg.id,
                            "delete_type": delete_type,
                            
                        }
                    )
            elif delete_type == "me":
                await sync_to_async(msg.deleted_for.add)(user)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "delete_message_event",
                        "message_id": msg.id,
                        "delete_type": delete_type,
                        
                    }
                )
        except Message.DoesNotExist:
            pass

        
        
    async def delete_message_event(self, event):
        await self.send(text_data=json.dumps({
            "action": "delete",
            "delete_type": event["delete_type"],
            "message_id": event["message_id"]
        }))
    
    
    async def like_message(self, message_id, user):
        print("Like Message Calling")

        try:
            msg = await sync_to_async(Message.objects.get)(id=message_id)

            # Check if user already liked the message
            liked = await sync_to_async(msg.likes.filter(id=user.id).exists)()

            if liked:
                await sync_to_async(msg.likes.remove)(user)
            else:
                await sync_to_async(msg.likes.add)(user)

            # Send like event to WebSocket group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "like_message_event",
                    "message_id": message_id,
                    "liked_by": user.username,
                    "likes_count": await sync_to_async(msg.likes.count)(),
                    "sender_channel": self.channel_name,
                }
            )

        except Message.DoesNotExist:
            pass  # Optionally handle/log error


    async def like_message_event(self, event):
        print("Like Message Event Calling2")
        if event.get("sender_channel") == self.channel_name:
            return
        await self.send(text_data=json.dumps({
            "action": "like",
            "message_id": event["message_id"],
            "liked_by": event["liked_by"],
            "likes_count": event["likes_count"]
        }))


# -----------------------------------------------------------------------------------------------------------------------------------------------------------
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        print("Consumers-RoomName:", self.room_name)
        self.group_name = f"chat_{self.room_name}"
        print("Consumers-GroupName:", self.group_name)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        # print(f'🔒rason for🛅 {close_code}')
    
    async def receive(self, text_data): #{"text": "hey", "reply_to":null or "text_reply"}
        # print('un_trans',text_data)
        data = json.loads(text_data)
        # print('transfer',data)
        sender = self.scope['user']
        # print('sender',sender)
        text = data.get("text", "").strip()
        # print('text:',text)
        action = data.get("action", None)
        print("action", action)
        reply_to_id = data.get("reply_to", None)
        print("reply_to",reply_to_id)
        message_id = data.get("message_id", None)
        print('messageIdFromRecieve', message_id)
        
        if action == "delete":
            delete_type = data.get("delete_type")
            messageid = data.get("message_id")
            print('DelelteMessagesId', messageid)
            await self.delete_message(message_id, sender, delete_type)
            return
        
        if action == "like":
            await self.like_message(message_id, sender)
            return
        
        usernames = self.room_name.split("_")[1:]
        receiver_username = [u for u in usernames if u != sender.username][0]
        receiver = await sync_to_async(User.objects.get)(username=receiver_username)
        msg = await self.save_message(sender, receiver, text, reply_to_id)
        await self.channel_layer.group_send(
            self.group_name,{
                "type": "chat_message",
                "id": msg.id,
                "text": text,
                "sender":sender.username,
                "reply_to": reply_to_id
            }
        )
    
    async def chat_message(self, event):
        # print('Problem is chat_message:')
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "text": event["text"],
            "sender": event["sender"],
            "reply_to": event["reply_to"],
        }))
        
    @sync_to_async
    def save_message(self, sender, receiver, text, reply_to_id):
        print('SaveMessagecalling')
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id)
            except Message.DoesNotExist:
                pass
        return Message.objects.create(sender=sender, receiver=receiver, text=text, reply_to=reply_to)
    
    #
    async def delete_message(self, msg_id, user, delete_type):
        print("Delete Message Calling")
        try:
            msg = await sync_to_async(Message.objects.select_related("sender").get)(id=msg_id)
            if delete_type == "everyone":
                if msg.sender_id == user.id:
                    msg.is_deleted = True
                    await sync_to_async(msg.save, thread_sensitive=True)()
                    
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "delete_message_event",
                            "message_id": msg.id,
                            "delete_type": delete_type,
                            
                        }
                    )
            elif delete_type == "me":
                await sync_to_async(msg.deleted_for.add)(user)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "delete_message_event",
                        "message_id": msg.id,
                        "delete_type": delete_type,
                        
                    }
                )
        except Message.DoesNotExist:
            pass
        
        
    async def delete_message_event(self, event):
        print('Delete Event')
        await self.send(text_data=json.dumps({
            "action": "delete",
            "delete_type": event["delete_type"],
            "message_id": event["message_id"]
        }))
    
    async def like_message(self, message_id, user):
        print("Like Message Calling")

        try:
            msg = await sync_to_async(Message.objects.get)(id=message_id)
            
            if await sync_to_async(lambda: user in msg.likes.all())():
                await sync_to_async(msg.likes.remove)(user)
            else:
                await sync_to_async(msg.likes.add)(user)

            await sync_to_async(msg.save, thread_sensitive=True)()


            # Send like event to WebSocket group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "like_message_event",
                    "message_id": message_id,
                    "liked_by": user.username,
                    "likes_count": await sync_to_async(msg.likes.count)(),
                }
            )


        except Message.DoesNotExist:
            pass  # Handle the error properly if needed
    
    async def like_message_event(self, event):
        print("Like Message Event Calling2")

        """ Send like update to the frontend """
        await self.send(text_data=json.dumps({
            "action": "like",
            "message_id": event["message_id"],
            "liked_by": event["liked_by"],
            "likes_count": event["likes_count"]
        }))
        

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
