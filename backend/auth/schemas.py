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

class PublicUserRegister(BaseModel):
    username: str
    email: Optional[str] = None
    fullname: Optional[str] = None
    password: str

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    fullname: Optional[str] = None
    profile_picture: Optional[str] = None
    disabled: Optional[bool] = None
    roles: Optional[List[Role]] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    fullname: Optional[str] = None
    profile_picture: Optional[str] = None
    disabled: Optional[bool] = False
    roles: List[str] = []

class UserListOut(BaseModel):
    users: List[UserOut]
    skip: int
    page_size: int
    total: int

class ProfilePictureOut(BaseModel):
    profile_picture: str 