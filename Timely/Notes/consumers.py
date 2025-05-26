import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TodoGroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_uuid = self.scope['url_route']['kwargs']['group_uuid']
        self.room_group_name = f'todo_{self.group_uuid}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # when client sends data to WebSocket
        data = json.loads(text_data)

        # Broadcast to all other clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'todo_update',
                'message': data['message']
            }
        )

    async def todo_update(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
