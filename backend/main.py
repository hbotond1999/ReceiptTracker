from fastapi import FastAPI
from auth.routes import router as auth_router
from sqlmodel import SQLModel, Session, select
from auth.routes import engine
from auth.models import Role
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    
    # Create default roles if they don't exist
    with Session(engine) as session:
        # Check if admin role exists
        admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
        if not admin_role:
            admin_role = Role(name="admin")
            session.add(admin_role)
            print("Admin role created")
        
        # Check if user role exists
        user_role = session.exec(select(Role).where(Role.name == "user")).first()
        if not user_role:
            user_role = Role(name="user")
            session.add(user_role)
            print("User role created")
        
        session.commit()
        print("Default roles initialized")

app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 