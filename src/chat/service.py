from fastapi import WebSocket
import redis.asyncio as aioredis
from src.config import Config


class ChannelsManager():
    def __init__(self):
        self.redis = aioredis.StrictRedis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db= 0,
            decode_responses=True
        )
    def make_2user_channel_id(self, user1, user2):
        return "-".join(sorted([user1, user2]))
    
    async def add_user_to_channel(self, user_id, channel_id):
        await self.redis.sadd(f"Chan:{channel_id}", user_id)
        await self.redis.sadd(f"Usr:{user_id}", channel_id)

    async def get_channel_users(self, channel_id):
        members = await self.redis.smembers(f"Chan:{channel_id}")
        return [m for m in members]
    
    async def is_user_in_channel(self, user_id, channel_id):
        return await self.redis.sismember(f"Chan:{channel_id}", user_id)
    
    async def get_user_channels(self, user_id):
        channels = await self.redis.smembers(f"Usr:{user_id}")
        return [c for c in channels]
    
    async def remove_user_from_channel(self, user_id, channel_id):
        await self.redis.srem(f"Chan:{channel_id}", user_id)
        await self.redis.srem(f"Usr:{user_id}", channel_id)
    

class WebSocketsManager():
    def __init__(self):
        self.ConnectedUsers = {}
    def connect_user(self, user_id, web_socket:WebSocket):
        self.ConnectedUsers[user_id] = web_socket
    def disconnect_user(self, user_id):
        self.ConnectedUsers.pop(user_id, None)
    def get_socket(self, user_id) ->WebSocket:
        return self.ConnectedUsers.get(user_id)

class MessagesManager():
    def create_message(sender:str, channel:str, content:str, message_type:str="message"):
        return {"sender":sender, "channel":channel, "content":content, "message_type":message_type}
    
    def __init__(self, channels_manager, sockets_manager):
        self.channels_manager = channels_manager
        self.sockets_manager = sockets_manager
        self.ChannelMessages = {}
    
    async def get_channel_messages(self, channel_id): #This should be replaced with postgreSQL
        return self.ChannelMessages.get(channel_id, [])

    async def store_message(self, message): #This should be replaced with postgreSQL
        if message['channel'] not in self.ChannelMessages: 
            self.ChannelMessages[message['channel']] = []
        self.ChannelMessages[message['channel']].append(message)

    async def store_missed_message(self, user, message):
        pass

    async def sendMessage(self, message):
        users_to_send_to = await self.channels_manager.get_channel_users(message['channel'])
        for user in users_to_send_to:
            await self.store_message(message) #Store data in postgreSQL
            socket_to_send_to = self.sockets_manager.get_socket(user)
            if socket_to_send_to:
                await socket_to_send_to.send_json(message)
            else:
                await self.store_missed_message(user, message) #Store data in Redis for notifications
    
    async def sendNewChannelMessage(self, message, user):
        await self.sendMessage(message)