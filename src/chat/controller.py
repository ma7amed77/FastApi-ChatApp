from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.routing import APIRouter
from pydantic import ValidationError
import logging
import asyncio

from .service import MessagesManager, ChannelsManager, WebSocketsManager
from . import schema
from src.auth.utils import tokens_manager
from src.auth.service import get_usernames, get_user_by_email, get_user_by_uid
from src.auth.dependencies import AccessTokenBearer
from src.database import get_session

logger =  logging.getLogger(__name__)
access_token_bearer = AccessTokenBearer()

chat_router = APIRouter()
channels_router = APIRouter(prefix="/channels",tags=["Channels"])

channels_manager = ChannelsManager()
sockets_manager  = WebSocketsManager()
messages_manager = MessagesManager(channels_manager, sockets_manager)

@chat_router.websocket("/ws")
async def websocket_endpoint(web_socket:WebSocket, token:str = Query()):
    try:
        payload = tokens_manager.decode_jwt_token(token=token)
        if payload['refresh'] == True:
            await web_socket.close(code=1008)
            return
        user_id = payload['sub']
    except Exception as e:
        logger.warning("WebSocket auth failed: %s", e)
        await web_socket.close(code=1008)
        return
    await web_socket.accept()
    sockets_manager.connect_user(user_id=user_id, web_socket=web_socket)
    await channels_manager.add_user_to_channel(user_id=user_id, channel_id='global')
    try:
        while True:
            data = await web_socket.receive_text()
            try:
                message = schema.RequestMessage.model_validate_json(data)
            except ValidationError as e:
                await web_socket.send_json({"error": "Invalid message format", "details": e.errors()})
                continue
            await messages_manager.send_message(MessagesManager.create_message(user_id, message.channel_id, message.content)) 

    except WebSocketDisconnect as e:
        sockets_manager.disconnect_user(user_id)
        
    except Exception as e:
        logger.error("Unexpected WebSocket error: %s", e, exc_info=True)
        sockets_manager.disconnect_user(user_id)
        await web_socket.close(code=1011)


@channels_router.get("/", response_model=schema.ChannelsList)
async def get_channels(user_details = Depends(access_token_bearer)):
    channels = await channels_manager.get_user_channels(user_details['sub'])
    return {"channels": channels}

@channels_router.get("/{channel_id}", response_model=schema.ChannelMessages)
async def get_channel_messages(channel_id: str, user_details = Depends(access_token_bearer), session:AsyncSession = Depends(get_session)):
    if not await channels_manager.is_user_in_channel(user_details['sub'], channel_id):
        raise HTTPException(status_code=403, detail="User is not a member of this channel.")
    
    messages = await messages_manager.get_channel_messages(channel_id)
    users_uids = await channels_manager.get_channel_users(channel_id)
    users_dict = await get_usernames(users_uids, session)
    return {"messages": messages, "users":users_dict}

@channels_router.post("/invite")
async def invite_user(request_data: schema.InviteUserData, user_details = Depends(access_token_bearer)):
    added_user_id = request_data.added_user_id
    channel_id = request_data.channel_id
    await channels_manager.add_user_to_channel(added_user_id, channel_id)
    message = MessagesManager.create_message("system", channel_id, f"{user_details['sub']} invited {added_user_id}", message_type = "new_channel")
    await messages_manager.sendNewChannelMessage(message, added_user_id)
    return {"message": f"User {added_user_id} joined channel {channel_id}."}

@channels_router.post("/create_group", response_model=schema.ResponseChannel)
async def create_group(request_data: schema.NewChannelData, user_details = Depends(access_token_bearer)):
    channel_id = request_data.channel_name
    await channels_manager.add_user_to_channel(user_details['sub'], channel_id)
    message = MessagesManager.create_message("system", channel_id, f"{user_details['sub']} Created a group", message_type = "new_channel")
    await messages_manager.sendNewChannelMessage(message, user_details['sub'])
    return {"channel_id":channel_id,"channel_name":channel_id}

@channels_router.post("/add_contact")
async def add_contact(request_data:schema.ContactUserData, user_details = Depends(access_token_bearer), session:AsyncSession = Depends(get_session)):
    this_user, added_user = await asyncio.gather(get_user_by_uid(user_details['sub'], session), get_user_by_email(request_data.user_email, session))
    if added_user is None:
        raise HTTPException(status_code=404, detail="No user with this email")
    channel_id = channels_manager.make_2user_channel_id(user_details['sub'], str(added_user.uid))
    message = MessagesManager.create_message("system", channel_id, f"{this_user.username} invited you", message_type = "new_channel")
    await asyncio.gather(channels_manager.add_user_to_channel(user_details['sub'], channel_id), channels_manager.add_user_to_channel(str(added_user.uid), channel_id))
    #await asyncio.gather(messages_manager.sendNewChannelMessage(message, user_details['sub']), messages_manager.sendNewChannelMessage(message, str(added_user.uid)))
    messages_manager.sendNewChannelMessage(message, user_details['sub'])
    return {"message": f"User {user_details['sub']} added to channel {channel_id}."}