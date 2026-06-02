from fastapi.security import HTTPBearer
from fastapi import status, HTTPException, Request
from .utils import tokens_manager


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request:Request) -> dict:
        creds = await super().__call__(request)
        token = creds.credentials

        try:
            token_data = tokens_manager.decode_jwt_token(token)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        await self.verify_token_data(token_data)
        return token_data
    
    async def verify_token_data(self, token_data):
        raise NotImplementedError("This should be overwriten")

class AccessTokenBearer(TokenBearer):
    async def verify_token_data(self, token_data):
        if token_data["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                                detail="Please provide an access token")

class RefreshTokenBearer(TokenBearer):
    async def verify_token_data(self, token_data):
        if not token_data["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                                detail="Please provide a refresh token")
        is_valid = await tokens_manager.is_token_valid(token_data["jti"])
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                                detail="Invalid token")