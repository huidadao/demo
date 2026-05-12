"""FastAPI application entry point."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.api.auth import router as auth_router
from app.logging import TransactionLoggingMiddleware

# Create FastAPI app
app = FastAPI(
    title="User Authentication API",
    description="Full-stack user authentication system",
    version="1.0.0",
)

# Transaction logging middleware (must be added before CORS to capture all requests)
app.add_middleware(TransactionLoggingMiddleware)

# CORS middleware configuration - allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


# Include routers
app.include_router(auth_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "User Authentication API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
