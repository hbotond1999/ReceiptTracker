import sys
import os
from getpass import getpass
from sqlmodel import Session, select, create_engine
from auth.models import User, Role, RoleEnum
from auth.utils import get_password_hash, get_user_by_username
from dotenv import load_dotenv

def main():
    # Ha van parancssori argumentum, azt használja DATABASE_URL-ként
    DATABASE_URL = None
    if len(sys.argv) > 1:
        DATABASE_URL = sys.argv[1]
        print(f"Database URL használata: {DATABASE_URL}")
    else:
        # Fallback to .env file loading
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        print(f"Database URL .env-ből: {DATABASE_URL}")
    
    # Database setup
    engine = create_engine(DATABASE_URL)
    
    username = input("Admin felhasználónév: ")
    email = input("Email: ")
    fullname = input("Teljes név: ")
    password = getpass("Jelszó: ")
    with Session(engine) as session:
        if get_user_by_username(session, username):
            print("Hiba: már létezik ilyen felhasználó.")
            sys.exit(1)
        # Lekérjük vagy létrehozzuk az admin szerepkört
        admin_role = session.exec(select(Role).where(Role.name == RoleEnum.admin)).first()
        if not admin_role:
            admin_role = Role(name=RoleEnum.admin)
            session.add(admin_role)
            session.commit()
            session.refresh(admin_role)
        user = User(
            username=username,
            email=email,
            fullname=fullname,
            hashed_password=get_password_hash(password),
            roles=[admin_role],
            disabled=False
        )
        session.add(user)
        session.commit()
        print(f"Admin user létrehozva: {username}")

if __name__ == "__main__":
    main() 