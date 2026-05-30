from fastapi import WebSocket, WebSocketDisconnect, Query
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .service import MessagesManager, ChannelsManager, WebSocketsManager
import logging

logger =  logging.getLogger(__name__)

chat_router = APIRouter()

messages_manager = MessagesManager()
@chat_router.on_event("startup")
async def startup():
    await messages_manager.channels_manager.creat_channel('global')

@chat_router.websocket("/ws")
async def websocket_endpoint(web_socket:WebSocket, user_id:str = Query()):
    await web_socket.accept()
    messages_manager.sockets_manager.connect_user(user_id=user_id, web_socket=web_socket)
    await messages_manager.channels_manager.add_user_to_channel(user_id=user_id, channel_id='global')
    try:
        while True:
            data = await web_socket.receive_text()

            if not data or not data.strip():
                continue

            await messages_manager.sendMessage(MessagesManager.create_message(user_id, "global", data)) 

    except WebSocketDisconnect as e:
        messages_manager.sockets_manager.disconnect_user(user_id)
        
    except Exception as e:
        logger.error("Unexpected WebSocket error: %s", e, exc_info=True)
        messages_manager.sockets_manager.disconnect_user(user_id)
        await web_socket.close(code=1011)