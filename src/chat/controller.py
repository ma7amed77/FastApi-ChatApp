from fastapi import WebSocket, WebSocketDisconnect, Query
from fastapi.routing import APIRouter
from .service import MessagesManager, ChannelsManager, WebSocketsManager
import logging

logger =  logging.getLogger(__name__)

chat_router = APIRouter()
channels_router = APIRouter(prefix="/channels",tags=["Channels"])

channels_manager = ChannelsManager()
sockets_manager  = WebSocketsManager()
messages_manager = MessagesManager(channels_manager, sockets_manager)

@chat_router.on_event("startup")
async def startup():
    await messages_manager.channels_manager.creat_channel('global')

@chat_router.websocket("/ws")
async def websocket_endpoint(web_socket:WebSocket, user_id:str = Query()):
    await web_socket.accept()
    sockets_manager.connect_user(user_id=user_id, web_socket=web_socket)
    await channels_manager.add_user_to_channel(user_id=user_id, channel_id='global')
    try:
        while True:
            data = await web_socket.receive_json()

            if not data:
                continue

            await messages_manager.sendMessage(MessagesManager.create_message(user_id, data["channel_id"], data["message"])) 

    except WebSocketDisconnect as e:
        sockets_manager.disconnect_user(user_id)
        
    except Exception as e:
        logger.error("Unexpected WebSocket error: %s", e, exc_info=True)
        sockets_manager.disconnect_user(user_id)
        await web_socket.close(code=1011)


@channels_router.get("/")
async def get_channels(user_id: str = Query()):
    channels = await channels_manager.get_user_channels(user_id)
    return {"channels": channels}

@channels_router.get("/{channel_id}")
async def get_channel_messages(channel_id: str, user_id: str = Query()):
    if not channels_manager.is_user_in_channel(user_id, channel_id):
        return {"error": "User is not a member of this channel."}
    
    messages = await messages_manager.get_channel_messages(channel_id)
    return {"messages": messages}

@channels_router.post("/invite/{channel_id}")
async def invite_user(channel_id: str, user_id: str = Query(), added_user_id: str = Query()):
    await channels_manager.add_user_to_channel(added_user_id, channel_id)
    message = MessagesManager.create_message("system", channel_id, f"{user_id} invited {added_user_id}", message_type = "new_channel")
    await messages_manager.sendNewChannelMessage(message, added_user_id)
    return {"message": f"User {added_user_id} joined channel {channel_id}."}

@channels_router.post("/create_group")
async def create_group(user_id: str = Query(), channel_id: str = Query()):
    await channels_manager.creat_channel(channel_id)
    await channels_manager.add_user_to_channel(user_id, channel_id)
    message = MessagesManager.create_message("system", channel_id, f"{user_id} Created a group", message_type = "new_channel")
    await messages_manager.sendNewChannelMessage(message, user_id)
    return {"message": f"Created channel with id {channel_id}."}

@channels_router.post("/add_contact")
async def add_contact(user_id: str = Query(), added_user_id: str = Query()):
    channel_id = await channels_manager.make_2user_channel_id(user_id, added_user_id)
    await channels_manager.creat_channel(channel_id)
    message = MessagesManager.create_message("system", channel_id, f"{user_id} invited you", message_type = "new_channel")
    await channels_manager.add_user_to_channel(user_id, channel_id)
    await channels_manager.add_user_to_channel(added_user_id, channel_id)
    await messages_manager.sendNewChannelMessage(message, user_id)
    await messages_manager.sendNewChannelMessage(message, added_user_id)
    return {"message": f"User {user_id} added to channel {channel_id}."}