from pydantic import BaseModel
from typing import List

class NewChannelData(BaseModel):
    channel_name:str

class ContactUserData(BaseModel):
    user_id:str

class InviteUserData(BaseModel):
    channel_id:str
    added_user_id:str

class RequestMessage(BaseModel):
    channel_id:str
    content:str

class ResponseMessage(BaseModel):
    sender:str
    channel:str
    content:str
    message_type:str

class ResponseChannel(BaseModel):
    channel_id:str
    channel_name:str

class ChannelsList(BaseModel):
    channels:List[ResponseChannel]

class ChannelMessages(BaseModel):
    messages:List[ResponseMessage]