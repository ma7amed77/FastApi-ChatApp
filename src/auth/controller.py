from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from . import service 

from .schema import UserRegisterModel, UserLoginModel
from src.database import get_session
from .dependencies import RefreshTokenBearer
from .utils import tokens_manager


refresh_token_bearer = RefreshTokenBearer()

auth_router =  APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post('/signup')
async def create_user_account(user_data:UserRegisterModel, session:AsyncSession = Depends(get_session)):
    try:
        new_user = await service.create_user(user_data, session)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exist")
    return new_user 

@auth_router.post('/login')
async def login_user(login_data:UserLoginModel, session:AsyncSession = Depends(get_session)):
    result = await service.login(login_data=login_data, session=session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or Password is wrong")
    return result

@auth_router.post('/logout')
async def logout_user(refresh_token_details:dict = Depends(refresh_token_bearer)):
    pass #TODO This needs to be implemented

@auth_router.post('/refresh')
async def refresh_access_token(refresh_token_details:dict = Depends(refresh_token_bearer)):
    new_access_token = tokens_manager.create_jwt_token(refresh_token_details['sub'], refresh_token_details["user"])
    return {"access_token": new_access_token}