import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SomeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Kết nối đến WebSocket thành công
        await self.accept()

    async def disconnect(self, close_code):
        # Kết nối đến WebSocket bị đóng
        pass

    async def receive(self, text_data):
        # Nhận yêu cầu cập nhật từ client
        data = json.loads(text_data)
        # Xử lý dữ liệu và lấy dữ liệu mới nhất
        # ...
        # Gửi dữ liệu mới nhất về client
        await self.send(text_data=json.dumps({'your_data': data}))