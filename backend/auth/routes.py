from fastapi import APIRouter, Depends, HTTPException, status, Security, Query, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from datetime import timedelta

from sqlalchemy import func

from . import utils, schemas
from sqlmodel import Session, create_engine, select
from .models import User as DBUser, Role
import os
from dotenv import load_dotenv
import shutil
from .schemas import UserOut, UserListOut, ProfilePictureOut, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

PROFILE_PIC_DIR = "profile_pics"
os.makedirs(PROFILE_PIC_DIR, exist_ok=True)

def get_session():
    with Session(engine) as session:
        yield session

def authenticate_user(session: Session, username: str, password: str):
    user = utils.get_user_by_username(session, username)
    if not user:
        return None
    if not utils.verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = utils.create_access_token(data={"sub": user.username, "roles": [role.name for role in user.roles]})
    refresh_token = utils.create_refresh_token(data={"sub": user.username, "roles": [role.name for role in user.roles]}, session=session)
    return TokenOut(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh", response_model=TokenOut)
def refresh_token(refresh_token: str, session: Session = Depends(get_session)):
    payload = utils.decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token type")
    username = payload.get("sub")
    if not utils.is_refresh_token_valid(refresh_token, session):
        raise HTTPException(status_code=401, detail="Refresh token not found or already used")
    new_access_token = utils.create_access_token(data={"sub": username, "roles": payload.get("roles", [])})
    new_refresh_token = utils.rotate_refresh_token(refresh_token, {"sub": username, "roles": payload.get("roles", [])}, session=session)
    return TokenOut(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

# Role-based dependency példa
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer()), session: Session = Depends(get_session)):
    token = credentials.credentials
    payload = utils.decode_token(token)
    username = payload.get("sub")
    user = utils.get_user_by_username(session, username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_roles(required_roles: list):
    def role_checker(user: DBUser = Depends(get_current_user)):
        if not any(role in [r.name for r in user.roles] for role in required_roles):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
    return role_checker

@router.post("/register", response_model=UserOut, dependencies=[Depends(require_roles(["admin"]))])
def register_user(user: schemas.UserInDB, session: Session = Depends(get_session)):
    # Ellenőrizzük, hogy a felhasználónév már létezik-e
    if utils.get_user_by_username(session, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Get default user role from database
    default_role = session.exec(select(Role).where(Role.name == "user")).first()
    if not default_role:
        raise HTTPException(status_code=500, detail="Default user role not found")
    
    # Get roles from user input or use default
    roles_to_assign = []
    if user.roles:
        for role_name in user.roles:
            role = session.exec(select(Role).where(Role.name == role_name)).first()
            if role:
                roles_to_assign.append(role)
    else:
        roles_to_assign.append(default_role)
    
    db_user = DBUser(
        username=user.username,
        email=user.email,
        fullname=user.fullname,
        profile_picture=user.profile_picture,
        hashed_password=utils.get_password_hash(user.hashed_password),
        disabled=user.disabled or False,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Assign roles after user is created
    db_user.roles = roles_to_assign
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return UserOut(
        id=db_user.id or 0,
        username=db_user.username,
        email=db_user.email,
        fullname=db_user.fullname,
        profile_picture=db_user.profile_picture,
        disabled=db_user.disabled,
        roles=[role.name for role in db_user.roles]
    )

@router.get("/users", response_model=UserListOut)
def list_users(
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: DBUser = Depends(require_roles(["admin"]))
):
    total = session.exec(select(func.count(DBUser.id))).one()
    statement = select(DBUser).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return UserListOut(
        users=[UserOut(
            id=u.id or 0,
            username=u.username,
            email=u.email,
            fullname=u.fullname,
            profile_picture=u.profile_picture,
            disabled=u.disabled,
            roles=[role.name for role in u.roles]
        ) for u in users],
        skip=skip,
        page_size=limit,
        total=total
    )

@router.post("/profile-picture", response_model=ProfilePictureOut)
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: DBUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(PROFILE_PIC_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Update user profile_picture
    current_user.profile_picture = file_path
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return ProfilePictureOut(profile_picture=file_path)

@router.get("/me", response_model=UserOut)
def get_me(current_user: DBUser = Depends(get_current_user)):
    return UserOut(
        id=int(current_user.id or 0),
        username=current_user.username,
        email=current_user.email,
        fullname=current_user.fullname,
        profile_picture=current_user.profile_picture,
        disabled=current_user.disabled,
        roles=[role.name for role in current_user.roles]
    ) 