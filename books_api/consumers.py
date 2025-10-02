# # books/consumers.py
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import Notification
#
#
# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_group_name = 'notifications'
#
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )
#
#     async def receive(self, text_data):
#         pass
#
#     async def notification_message(self, event):
#         message = event['message']
#
#         await self.send(text_data=json.dumps({
#             'message': message
#         }))