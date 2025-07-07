import time

from fastapi import FastAPI, Request
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

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(auth_router)
app.include_router(receipt_router)
app.include_router(statistic_router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 