from fastapi import WebSocket

class ChannelsManager():
    def __init__(self):
        self.ChannelsUsers = {}
    #This should be replaced with redis so I am making them async to not have bugs later
    async def creat_channel(self, channel_id):
        self.ChannelsUsers[channel_id] = set()
    async def add_user_to_channel(self, user_id, channel_id):
        self.ChannelsUsers[channel_id].add(user_id)
    async def get_channel_users(self, channel_id):
        return [socket for socket in self.ChannelsUsers[channel_id]]

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
    def create_message(sender:str, channel:str, content:str):
        return {"sender":sender, "channel":channel, "content":content}
    
    def __init__(self):
        self.channels_manager = ChannelsManager()
        self.sockets_manager = WebSocketsManager()

    async def store_message(self, message):
        pass

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
