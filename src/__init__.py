from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.redis import RateLimiter
from .chat.controller import chat_router, channels_router
from .auth.controller import auth_router
from .database import init_db

@asynccontextmanager
async def life_span(app:FastAPI):
    print("Server is Starting ..... ")
    await init_db()
    yield
    print("Server Stopped :(")

app = FastAPI(lifespan=life_span)
rate_limiter = RateLimiter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    key = f"{request.client.host}:{request.url.path}"
    if await rate_limiter(key):
        return response
    else:
        return Response('You reached rate limit', status_code=429)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/',tags=["Pages"])
async def login_page():
    return FileResponse('static/login.html')

@app.get('/chat', tags=["Pages"])
async def chat_page():
    return FileResponse('static/chat.html')

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(channels_router)