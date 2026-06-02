from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from functools import partial

email_field = partial(Field, default="someone@gmail.com")

class UserRegisterModel(BaseModel):
    username:str = Field(default="username", max_length=16)
    email:EmailStr = email_field()
    password:str = Field(default="password", min_length=4)

class UserLoginModel(BaseModel):
    email:EmailStr = email_field()
    password:str = Field(default="password", min_length=4)
