import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        await self.channel_layer.group_add(f"job_{self.job_id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"job_{self.job_id}", self.channel_name)

    async def job_update(self, event):
        await self.send(text_data=json.dumps({
            'progress': event['progress'],
            'message': event['message']
        }))
