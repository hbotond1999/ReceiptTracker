from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from auth.routes import router as auth_router
from receipt.routes import router as receipt_router
from statistic.routes import router as statistic_router
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
app.include_router(auth_router)
app.include_router(receipt_router)
app.include_router(statistic_router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 