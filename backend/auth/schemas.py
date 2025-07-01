from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class Role(str, Enum):
    admin = "admin"
    user = "user"

class User(BaseModel):
    username: str
    email: Optional[str] = None
    fullname: Optional[str] = None
    profile_picture: Optional[str] = None
    disabled: Optional[bool] = None
    roles: List[Role] = []

class UserInDB(User):
    hashed_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    username: str
    email: Optional[str] = None
    fullname: Optional[str] = None
    profile_picture: Optional[str] = None
    disabled: Optional[bool] = None
    roles: List[Role] = []

class UserListOut(BaseModel):
    users: List[UserOut]
    skip: int
    page_size: int
    total: int

class ProfilePictureOut(BaseModel):
    profile_picture: str 