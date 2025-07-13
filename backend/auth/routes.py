from fastapi import APIRouter, Depends, HTTPException, status, Security, Query, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import func

from sqlmodel import Session, create_engine, select
import os
from dotenv import load_dotenv
import shutil

from auth import utils, schemas
from auth.schemas import TokenOut, UserOut, UserListOut, ProfilePictureOut, UserUpdateRequest, PublicUserRegister
from auth.models import User as DBUser, Role

router = APIRouter(prefix="/auth", tags=["auth"])

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)

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
def register_user_admin(user: schemas.UserInDB, session: Session = Depends(get_session)):
    # Ellenőrizzük, hogy a felhasználónév már létezik-e
    if utils.get_user_by_username(session, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    default_role = session.exec(select(Role).where(Role.name == "user")).first()
    if not default_role:
        raise HTTPException(status_code=500, detail="Default user role not found")
    
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

@router.post("/register/public", response_model=UserOut)
def register_user_public(user: PublicUserRegister, session: Session = Depends(get_session)):
    # Ellenőrizzük, hogy a felhasználónév már létezik-e
    if utils.get_user_by_username(session, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Ellenőrizzük, hogy az email már nem foglalt-e (ha meg van adva)
    if user.email:
        existing_user = session.exec(select(DBUser).where(DBUser.email == user.email)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    default_role = session.exec(select(Role).where(Role.name == "user")).first()
    if not default_role:
        raise HTTPException(status_code=500, detail="Default user role not found")
    
    db_user = DBUser(
        username=user.username,
        email=user.email,
        fullname=user.fullname,
        profile_picture=None,
        hashed_password=utils.get_password_hash(user.password),
        disabled=False,  # Publikus regisztráció esetén mindig aktív
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Assign default user role
    db_user.roles = [default_role]
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
    username: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    current_user: DBUser = Depends(require_roles(["admin"]))
):
    total = session.exec(select(func.count()).select_from(DBUser)).one()
    statement = select(DBUser)
    if username:
        statement = statement.where(DBUser.username.ilike(f"%{username}%"))
    statement = statement.offset(skip).limit(limit)
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

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_user: DBUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Ellenőrizzük, hogy a felhasználó admin-e vagy saját magát frissíti-e
    is_admin = any(role.name == "admin" for role in current_user.roles)
    is_own_profile = current_user.id == user_id
    
    if not is_admin and not is_own_profile:
        raise HTTPException(status_code=403, detail="You can only update your own profile or need admin privileges")
    
    # Megkeressük a frissítendő felhasználót
    statement = select(DBUser).where(DBUser.id == user_id)
    user_to_update = session.exec(statement).first()
    
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ha nem admin és saját magát frissíti, akkor nem módosíthatja a disabled státust és a role-okat
    if not is_admin:
        if user_update.disabled is not None:
            raise HTTPException(status_code=403, detail="You cannot change your disabled status")
        if user_update.roles is not None:
            raise HTTPException(status_code=403, detail="You cannot change your roles")
    
    # Frissítjük a felhasználó adatait
    if user_update.email is not None:
        # Ellenőrizzük, hogy az email már nem foglalt-e (kivéve ha ugyanaz a felhasználó)
        if user_update.email != user_to_update.email:
            existing_user = session.exec(select(DBUser).where(DBUser.email == user_update.email)).first()
            if existing_user and existing_user.id != user_id:
                raise HTTPException(status_code=400, detail="Email already registered")
        user_to_update.email = user_update.email
    
    if user_update.fullname is not None:
        user_to_update.fullname = user_update.fullname
    
    if user_update.profile_picture is not None:
        user_to_update.profile_picture = user_update.profile_picture
    
    if user_update.disabled is not None and is_admin:
        user_to_update.disabled = user_update.disabled
    
    # Role-ok frissítése (csak admin számára)
    if user_update.roles is not None and is_admin:
        roles_to_assign = []
        for role_name in user_update.roles:
            role = session.exec(select(Role).where(Role.name == role_name)).first()
            if role:
                roles_to_assign.append(role)
        if roles_to_assign:
            user_to_update.roles = roles_to_assign
    
    session.add(user_to_update)
    session.commit()
    session.refresh(user_to_update)
    
    return UserOut(
        id=user_to_update.id or 0,
        username=user_to_update.username,
        email=user_to_update.email,
        fullname=user_to_update.fullname,
        profile_picture=user_to_update.profile_picture,
        disabled=user_to_update.disabled,
        roles=[role.name for role in user_to_update.roles]
    )

@router.delete("/users/{user_id}", response_model=TokenOut, dependencies=[Depends(require_roles(["admin"]))])
def delete_users(user_id: int, session: Session = Depends(get_session)):
    statement = select(DBUser).where(DBUser.id == user_id)
    user = session.exec(statement).one()
    if user:
        session.delete(user)
        session.commit()
        return
    else:
        raise HTTPException(status_code=404, detail="User not found")
