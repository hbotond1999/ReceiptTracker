import sys
import os
from sqlmodel import SQLModel, Session, select, create_engine
from auth.models import Role, RoleEnum
from dotenv import load_dotenv
from receipt.models import *

def init_database():
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
    
    """Initialize database tables and default data"""
    print("Initializing database...")
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("Database tables created")
    
    # Create default roles if they don't exist
    with Session(engine) as session:
        # Check if admin role exists
        admin_role = session.exec(select(Role).where(Role.name == RoleEnum.admin)).first()
        if not admin_role:
            admin_role = Role(name=RoleEnum.admin)
            session.add(admin_role)
            print("Admin role created")
        
        # Check if user role exists
        user_role = session.exec(select(Role).where(Role.name == RoleEnum.user)).first()
        if not user_role:
            user_role = Role(name=RoleEnum.user)
            session.add(user_role)
            print("User role created")
        
        session.commit()
        print("Default roles initialized")
    
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    init_database() 