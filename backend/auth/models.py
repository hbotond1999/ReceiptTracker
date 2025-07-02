from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"

class UserRoleLink(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)

class User(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, index=True, unique=True)
    fullname: Optional[str] = None
    profile_picture: Optional[str] = None  # Fájlrendszerbeli elérési út
    hashed_password: str
    disabled: bool = False
    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)

class Role(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: RoleEnum = Field(index=True, unique=True)
    users: List[User] = Relationship(back_populates="roles", link_model=UserRoleLink)

class RefreshToken(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    user_id: int = Field(foreign_key="user.id") 