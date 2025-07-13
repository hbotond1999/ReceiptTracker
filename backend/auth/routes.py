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
from app_logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize logger
logger = get_logger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)

PROFILE_PIC_DIR = "profile_pics"
os.makedirs(PROFILE_PIC_DIR, exist_ok=True)

def get_session():
    with Session(engine) as session:
        yield session

def authenticate_user(session: Session, username: str, password: str):
    logger.debug(f"Authenticating user: {username}")
    user = utils.get_user_by_username(session, username)
    if not user:
        logger.debug(f"User not found: {username}")
        return None
    if not utils.verify_password(password, user.hashed_password):
        logger.debug(f"Password verification failed for user: {username}")
        return None
    logger.debug(f"User authenticated successfully: {username}")
    return user

@router.post("/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    logger.info(f"Login attempt for user: {form_data.username}")
    logger.debug(f"Login request details - Username: {form_data.username}, Client ID: {form_data.client_id}")
    
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username} - Invalid credentials")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if user.disabled:
        logger.warning(f"Failed login attempt for user: {form_data.username} - User disabled")
        raise HTTPException(status_code=401, detail="User is disabled")
    
    logger.debug(f"Creating access token for user: {form_data.username}, roles: {[role.name for role in user.roles]}")
    logger.info(f"Successful login for user: {form_data.username}")
    access_token = utils.create_access_token(data={"sub": user.username, "roles": [role.name for role in user.roles]})
    refresh_token = utils.create_refresh_token(data={"sub": user.username, "roles": [role.name for role in user.roles]}, session=session)
    logger.debug(f"Tokens created successfully for user: {form_data.username}")
    return TokenOut(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh", response_model=TokenOut)
def refresh_token(refresh_token: str, session: Session = Depends(get_session)):
    logger.info("Token refresh attempt")
    logger.debug(f"Refresh token received: {refresh_token[:20]}...")
    
    try:
        payload = utils.decode_token(refresh_token)
        logger.debug(f"Token payload decoded: {payload}")
    except Exception as e:
        logger.error(f"Failed to decode refresh token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    if payload.get("type") != "refresh":
        logger.warning(f"Invalid refresh token type: {payload.get('type')}")
        raise HTTPException(status_code=401, detail="Invalid refresh token type")
    
    username = payload.get("sub")
    logger.debug(f"Refresh token for user: {username}")
    
    if not utils.is_refresh_token_valid(refresh_token, session):
        logger.warning(f"Refresh token not valid for user: {username}")
        raise HTTPException(status_code=401, detail="Refresh token not found or already used")
    
    logger.debug(f"Creating new tokens for user: {username}")
    new_access_token = utils.create_access_token(data={"sub": username, "roles": payload.get("roles", [])})
    new_refresh_token = utils.rotate_refresh_token(refresh_token, {"sub": username, "roles": payload.get("roles", [])}, session=session)
    logger.info(f"Token refresh successful for user: {username}")
    return TokenOut(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

# Role-based dependency példa
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer()), session: Session = Depends(get_session)):
    logger.debug("Getting current user from token")
    token = credentials.credentials
    logger.debug(f"Token received: {token[:20]}...")
    
    try:
        payload = utils.decode_token(token)
        logger.debug(f"Token payload: {payload}")
    except Exception as e:
        logger.error(f"Failed to decode access token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    logger.debug(f"Token belongs to user: {username}")
    
    user = utils.get_user_by_username(session, username)
    if user is None:
        logger.warning(f"User not found in database: {username}")
        raise HTTPException(status_code=401, detail="User not found")
    if user.disabled:
        logger.warning(f"User is disabled: {username}")
        raise HTTPException(status_code=401, detail="User is disabled")
    
    logger.debug(f"Current user retrieved successfully: {username}")
    return user

def require_roles(required_roles: list):
    def role_checker(user: DBUser = Depends(get_current_user)):
        user_roles = [r.name for r in user.roles]
        logger.debug(f"Checking roles for user {user.username}: required={required_roles}, user_roles={user_roles}")
        
        if not any(role in user_roles for role in required_roles):
            logger.warning(f"Insufficient permissions for user {user.username}: required={required_roles}, user_roles={user_roles}")
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        logger.debug(f"Role check passed for user {user.username}")
        return user
    return role_checker

@router.post("/register", response_model=UserOut, dependencies=[Depends(require_roles(["admin"]))])
def register_user_admin(user: schemas.UserInDB, session: Session = Depends(get_session)):
    logger.info(f"Admin registration attempt for user: {user.username}")
    logger.debug(f"Registration data: username={user.username}, email={user.email}, fullname={user.fullname}, roles={user.roles}")
    
    # Ellenőrizzük, hogy a felhasználónév már létezik-e
    if utils.get_user_by_username(session, user.username):
        logger.warning(f"Registration failed - username already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    logger.debug("Looking for default user role")
    default_role = session.exec(select(Role).where(Role.name == "user")).first()
    if not default_role:
        logger.error("Default user role not found in database")
        raise HTTPException(status_code=500, detail="Default user role not found")
    
    roles_to_assign = []
    if user.roles:
        logger.debug(f"Processing custom roles: {user.roles}")
        for role_name in user.roles:
            role = session.exec(select(Role).where(Role.name == role_name)).first()
            if role:
                roles_to_assign.append(role)
                logger.debug(f"Role found and added: {role_name}")
            else:
                logger.warning(f"Role not found: {role_name}")
    else:
        logger.debug("No custom roles specified, using default user role")
        roles_to_assign.append(default_role)
    
    logger.debug(f"Creating user in database: {user.username}")
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
    logger.debug(f"User created with ID: {db_user.id}")
    
    # Assign roles after user is created
    logger.debug(f"Assigning roles to user {user.username}: {[r.name for r in roles_to_assign]}")
    db_user.roles = roles_to_assign
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    logger.info(f"Admin registration successful for user: {user.username}")
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
    logger.info(f"Public registration attempt for user: {user.username}")
    logger.debug(f"Public registration data: username={user.username}, email={user.email}, fullname={user.fullname}")
    
    # Ellenőrizzük, hogy a felhasználónév már létezik-e
    if utils.get_user_by_username(session, user.username):
        logger.warning(f"Public registration failed - username already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Ellenőrizzük, hogy az email már nem foglalt-e (ha meg van adva)
    if user.email:
        logger.debug(f"Checking if email already exists: {user.email}")
        existing_user = session.exec(select(DBUser).where(DBUser.email == user.email)).first()
        if existing_user:
            logger.warning(f"Public registration failed - email already exists: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
    
    logger.debug("Looking for default user role for public registration")
    default_role = session.exec(select(Role).where(Role.name == "user")).first()
    if not default_role:
        logger.error("Default user role not found in database")
        raise HTTPException(status_code=500, detail="Default user role not found")
    
    logger.debug(f"Creating user in database: {user.username}")
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
    logger.debug(f"User created with ID: {db_user.id}")
    
    # Assign default user role
    logger.debug(f"Assigning default user role to: {user.username}")
    db_user.roles = [default_role]
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    logger.info(f"Public registration successful for user: {user.username}")
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
    logger.info(f"User list request by admin: {current_user.username}")
    logger.debug(f"List users parameters: username_filter={username}, skip={skip}, limit={limit}")
    
    logger.debug("Getting total user count")
    total = session.exec(select(func.count()).select_from(DBUser)).one()
    logger.debug(f"Total users in database: {total}")
    
    statement = select(DBUser)
    if username:
        logger.debug(f"Applying username filter: {username}")
        statement = statement.where(DBUser.username.ilike(f"%{username}%"))
    
    logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
    statement = statement.offset(skip).limit(limit)
    
    logger.debug("Executing user query")
    users = session.exec(statement).all()
    logger.debug(f"Retrieved {len(users)} users")
    
    result = UserListOut(
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
    
    logger.info(f"User list request completed - returned {len(result.users)} users")
    return result

@router.post("/profile-picture", response_model=ProfilePictureOut)
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: DBUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"Profile picture upload request from user: {current_user.username}")
    logger.debug(f"Upload details: filename={file.filename}, content_type={file.content_type}, size={file.size}")
    
    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(PROFILE_PIC_DIR, filename)
    logger.debug(f"Saving file to: {file_path}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.debug(f"File saved successfully: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save profile picture")
    
    # Update user profile_picture
    logger.debug(f"Updating user profile picture in database: {current_user.username}")
    current_user.profile_picture = file_path
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    logger.info(f"Profile picture upload successful for user: {current_user.username}")
    return ProfilePictureOut(profile_picture=file_path)

@router.get("/me", response_model=UserOut)
def get_me(current_user: DBUser = Depends(get_current_user)):
    logger.info(f"Get current user info request: {current_user.username}")
    logger.debug(f"User details: id={current_user.id}, email={current_user.email}, roles={[r.name for r in current_user.roles]}")
    
    result = UserOut(
        id=int(current_user.id or 0),
        username=current_user.username,
        email=current_user.email,
        fullname=current_user.fullname,
        profile_picture=current_user.profile_picture,
        disabled=current_user.disabled,
        roles=[role.name for role in current_user.roles]
    )
    
    logger.debug("Current user info retrieved successfully")
    return result

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_user: DBUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    logger.info(f"User update request: target_user_id={user_id}, requesting_user={current_user.username}")
    logger.debug(f"Update data: {user_update.dict(exclude_unset=True)}")
    
    # Ellenőrizzük, hogy a felhasználó admin-e vagy saját magát frissíti-e
    is_admin = any(role.name == "admin" for role in current_user.roles)
    is_own_profile = current_user.id == user_id
    
    logger.debug(f"Permission check: is_admin={is_admin}, is_own_profile={is_own_profile}")
    
    if not is_admin and not is_own_profile:
        logger.warning(f"Insufficient permissions for user update: user={current_user.username}, target_id={user_id}")
        raise HTTPException(status_code=403, detail="You can only update your own profile or need admin privileges")
    
    # Megkeressük a frissítendő felhasználót
    logger.debug(f"Looking for user to update: {user_id}")
    statement = select(DBUser).where(DBUser.id == user_id)
    user_to_update = session.exec(statement).first()
    
    if not user_to_update:
        logger.warning(f"User not found for update: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.debug(f"User found for update: {user_to_update.username}")
    
    # Ha nem admin és saját magát frissíti, akkor nem módosíthatja a disabled státust és a role-okat
    if not is_admin:
        if user_update.disabled is not None:
            logger.warning(f"Non-admin user tried to change disabled status: {current_user.username}")
            raise HTTPException(status_code=403, detail="You cannot change your disabled status")
        if user_update.roles is not None:
            logger.warning(f"Non-admin user tried to change roles: {current_user.username}")
            raise HTTPException(status_code=403, detail="You cannot change your roles")
    
    # Frissítjük a felhasználó adatait
    if user_update.email is not None:
        logger.debug(f"Updating email: {user_update.email}")
        # Ellenőrizzük, hogy az email már nem foglalt-e (kivéve ha ugyanaz a felhasználó)
        if user_update.email != user_to_update.email:
            logger.debug("Checking if new email already exists")
            existing_user = session.exec(select(DBUser).where(DBUser.email == user_update.email)).first()
            if existing_user and existing_user.id != user_id:
                logger.warning(f"Email already registered: {user_update.email}")
                raise HTTPException(status_code=400, detail="Email already registered")
        user_to_update.email = user_update.email
    
    if user_update.fullname is not None:
        logger.debug(f"Updating fullname: {user_update.fullname}")
        user_to_update.fullname = user_update.fullname
    
    if user_update.profile_picture is not None:
        logger.debug(f"Updating profile picture: {user_update.profile_picture}")
        user_to_update.profile_picture = user_update.profile_picture
    
    if user_update.disabled is not None and is_admin:
        logger.debug(f"Admin updating disabled status: {user_update.disabled}")
        user_to_update.disabled = user_update.disabled
    
    # Role-ok frissítése (csak admin számára)
    if user_update.roles is not None and is_admin:
        logger.debug(f"Admin updating roles: {user_update.roles}")
        roles_to_assign = []
        for role_name in user_update.roles:
            role = session.exec(select(Role).where(Role.name == role_name)).first()
            if role:
                roles_to_assign.append(role)
                logger.debug(f"Role found and will be assigned: {role_name}")
            else:
                logger.warning(f"Role not found: {role_name}")
        if roles_to_assign:
            user_to_update.roles = roles_to_assign
    
    logger.debug("Saving user updates to database")
    session.add(user_to_update)
    session.commit()
    session.refresh(user_to_update)
    
    logger.info(f"User update successful: {user_to_update.username}")
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
    logger.info(f"User deletion request: user_id={user_id}")
    logger.debug(f"Looking for user to delete: {user_id}")
    
    statement = select(DBUser).where(DBUser.id == user_id)
    user = session.exec(statement).one()
    if user:
        logger.debug(f"User found for deletion: {user.username}")
        session.delete(user)
        session.commit()
        logger.info(f"User deleted successfully: {user.username}")
        return
    else:
        logger.warning(f"User not found for deletion: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
