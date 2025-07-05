from sqlmodel import SQLModel, Session, select
from auth.routes import engine
from auth.models import Role, RoleEnum
from dotenv import load_dotenv
from receipt.models import *

load_dotenv()

def init_database():
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