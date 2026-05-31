from fastapi import WebSocket

class ChannelsManager():
    def __init__(self):
        self.ChannelsUsers = {}
    #This should be replaced with redis so I am making them async to not have bugs later
    async def make_2user_channel_id(self, user1, user2):
        return "-".join(sorted([user1, user2]))
    async def creat_channel(self, channel_id):
        self.ChannelsUsers[channel_id] = set()
        return channel_id
    async def add_user_to_channel(self, user_id, channel_id):
        self.ChannelsUsers[channel_id].add(user_id)
    async def get_channel_users(self, channel_id):
        return [socket for socket in self.ChannelsUsers[channel_id]]
    async def is_user_in_channel(self, user_id, channel_id):
        return user_id in self.ChannelsUsers.get(channel_id, set())
    async def get_user_channels(self, user_id):
        return [channel for channel, users in self.ChannelsUsers.items() if user_id in users]
    

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
