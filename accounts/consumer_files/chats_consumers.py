# accounts/consumer_files/chat_consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync, sync_to_async
# from .models import Message, Group
from models_folder.chat_models import *
from django.contrib.auth.models import User
from django.utils.timezone import now
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
# from .models import Group, Message

User = get_user_model()

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



#############################3-----------------------------------------------------------------

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