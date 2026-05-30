from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from .chat.controller import chat_router

logger =  logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/')
async def login_page():
    return FileResponse('static/login.html')

@app.get('/chat')
async def chat_page():
    return FileResponse('static/chat.html')

@app.post('/new_chat')
async def new_chat():
    return {"message": "This endpoint is a placeholder for creating new chats/groups."}

app.include_router(chat_router)