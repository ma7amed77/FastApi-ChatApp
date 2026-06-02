from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .schema import UserRegisterModel, UserLoginModel
from .models import User
from .utils import generate_hashed_password, verify_password, tokens_manager

async def get_user_by_email(email:str, session:AsyncSession):
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()

async def get_user_by_uid(uid:str, session:AsyncSession):
    statement = select(User).where(User.uid == uid)
    result = await session.exec(statement)
    return result.first()

async def create_user(user_data:UserRegisterModel, session:AsyncSession):
    user_data_dict = user_data.model_dump()
    new_user = User(**user_data_dict)
    new_user.password_hash = generate_hashed_password(user_data_dict['password'])
    session.add(new_user)
    await session.commit()

    user_data = {
            "email":new_user.email
            }
    access_token = tokens_manager.create_jwt_token(new_user.uid, user_data)
    refresh_token = tokens_manager.create_jwt_token(new_user.uid, user_data, refresh=True)
    return {
        "message": "Login Successful",
        "user_id":str(new_user.uid),
        "access_token":access_token,
        "refresh_token":refresh_token
    }

async def login(login_data:UserLoginModel, session:AsyncSession):
    user = await get_user_by_email(login_data.email, session)
    if user is None:
        return None
    if verify_password(login_data.password, user.password_hash):
        user_data = {
            "email":user.email
            }
        access_token = tokens_manager.create_jwt_token(user.uid, user_data)
        refresh_token = tokens_manager.create_jwt_token(user.uid, user_data, refresh=True)
        return {
            "message": "Login Successful",
            "user_id":str(user.uid),
            "access_token":access_token,
            "refresh_token":refresh_token
        }
    else:
        return None
    
async def get_usernames(uids: list[str], session:AsyncSession):
    statement = select(User).where(User.uid.in_(uids))
    result = await session.exec(statement)
    users = result.all()
    return {user.uid: user.username for user in users}