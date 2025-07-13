import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from auth.routes import router as auth_router
from receipt.routes import router as receipt_router
from statistic.routes import router as statistic_router
from dotenv import load_dotenv
import uvicorn

# Import logging configuration
from app_logging import configure_from_env, get_logger, set_request_id, generate_request_id

load_dotenv()

# Configure logging from environment variables
configure_from_env()

# Get logger for main application
logger = get_logger(__name__)

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
async def logging_middleware(request: Request, call_next):
    # Generate and set request ID
    request_id = generate_request_id()
    set_request_id(request_id)
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        
        # Log response
        logger.info(f"Response: {response.status_code} - Time: {process_time:.4f}s")
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error(f"Request failed: {str(e)} - Time: {process_time:.4f}s")
        raise


@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application shutting down...")

app.include_router(auth_router)
app.include_router(receipt_router)
app.include_router(statistic_router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 