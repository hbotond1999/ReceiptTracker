from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.auth.routes import router as auth_router
from backend.auth.models import Role, RoleEnum

from backend.receipt.routes import router as receipt_router
from sqlmodel import SQLModel, Session, select
from backend.auth.routes import engine

from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(
    title="Receipt Tracker API",
    description="API for managing receipts and markets",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    
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

app.include_router(auth_router)
app.include_router(receipt_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 