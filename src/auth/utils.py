from passlib.context import CryptContext
import jwt
import uuid
import redis.asyncio as aioredis
from datetime import datetime, timedelta
from src.config import Config

REFRESH_TOKEN_TIME = timedelta(days=2)
ACCESS_TOKEN_TIME = timedelta(minutes=60)

password_context = CryptContext(
            schemes=['argon2']
        )
def generate_hashed_password(password:str) -> str:
        hashed_password = password_context.hash(password)
        return hashed_password

def verify_password( password:str, hashed_password:str) -> bool:
        return password_context.verify(password, hashed_password)

class TokensManager():
    def __init__(self):
        self.redis = aioredis.StrictRedis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db= 1
        )

    @staticmethod
    def create_jwt_token(uid, user_data:dict, refresh:bool = False):
        payload = {
            'sub':str(uid),
            'exp':datetime.now() + (REFRESH_TOKEN_TIME if refresh else ACCESS_TOKEN_TIME),
            'user_data':user_data,
            'refresh':refresh,
            'jti':str(uuid.uuid4())
        }
        token = jwt.encode(
            payload=payload,
            key=Config.JWT_SECRET,
            algorithm=Config.JWT_ALGORITHM
        )
        return token
    
    @staticmethod
    def decode_jwt_token(token:str) -> dict:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    
    async def add_token_to_whitelist(self, jti:str) -> None:
        await self.redis.set(
            name = jti,
            value= 1,
            ex= int(REFRESH_TOKEN_TIME.total_seconds())
        )
    
    async def is_token_valid(self, jti:str) -> bool:
        jti = await self.redis.getdel(jti)
        return jti is not None

tokens_manager = TokensManager()