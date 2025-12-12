from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import auth, projects, tasks, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="TaskFlow API",
    description="Project Management Application - управление проектами и задачами",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(users.router)


@app.get("/healthcheck")
async def healthcheck():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200, content={"status": "healthy", "service": "taskflow-api"}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TaskFlow API", "docs": "/docs"}
