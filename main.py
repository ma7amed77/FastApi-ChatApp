from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

logger =  logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/')
async def geto():
    return FileResponse('static/index.html')

def create_message(sender:str, channel:str, content:str):
    return {"sender":sender, "channel":channel, "content":content}

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
    def __init__(self):
        self.channels_manager = ChannelsManager()
        self.sockets_manager = WebSocketsManager()

    async def store_message(user, message):
        pass

    async def store_missed_message(user, message):
        pass

    async def sendMessage(self, message):
        users_to_send_to = await self.channels_manager.get_channel_users(message['channel'])
        for user in users_to_send_to:
            self.store_message(user, message) #Store data in postgreSQL

            socket_to_send_to = self.sockets_manager.get_socket(user)
            if socket_to_send_to:
                await socket_to_send_to.send_json(message)
            else:
                self.store_missed_message(user, message) #Store data in Redis for notifications


messages_manager = MessagesManager()
@app.on_event("startup")
async def startup():
    await messages_manager.channels_manager.creat_channel('global')


@app.websocket("/ws")
async def websocket_endpoint(web_socket:WebSocket, user_id:str = Query()):
    await web_socket.accept()
    messages_manager.sockets_manager.connect_user(user_id=user_id, web_socket=web_socket)
    await messages_manager.channels_manager.add_user_to_channel(user_id=user_id, channel_id='global')
    try:
        while True:
            data = await web_socket.receive_text()

            if not data or not data.strip():
                continue

            await messages_manager.sendMessage(create_message(user_id, "global", data)) 

    except WebSocketDisconnect as e:
        messages_manager.sockets_manager.disconnect_user(user_id)
        
    except Exception as e:
        logger.error("Unexpected WebSocket error: %s", e, exc_info=True)
        messages_manager.sockets_manager.disconnect_user(user_id)
        await web_socket.close(code=1011)