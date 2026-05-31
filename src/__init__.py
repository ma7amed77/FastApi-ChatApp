from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from .chat.controller import chat_router, channels_router

logger =  logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/',tags=["Pages"])
async def login_page():
    return FileResponse('static/login.html')

@app.get('/chat', tags=["Pages"])
async def chat_page():
    return FileResponse('static/chat.html')

app.include_router(chat_router)
app.include_router(channels_router)