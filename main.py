from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.models.certificate import (
    Certificate, User, Institution, VerificationLog
)
from app.api import admin, verifier
from app.api.auth import router as auth_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Certificate Verification System",
    description="Tamil Nadu Academic Certificate Verification",
    version="1.0.0"
)

# CORS - allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routers
app.include_router(auth_router)
app.include_router(admin.router)
app.include_router(verifier.router)


@app.get("/")
def home():
    return FileResponse("templates/index.html")

@app.get("/login")
@app.get("/login.html")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/institution")
@app.get("/institution.html")
def institution_page():
    return FileResponse("templates/institution.html")

@app.get("/student")
@app.get("/student.html")
def student_page():
    return FileResponse("templates/student.html")

@app.get("/verifier")
@app.get("/verifier.html")
def verifier_page():
    return FileResponse("templates/verifier.html")

@app.get("/admin-panel")
@app.get("/admin.html")
def admin_page():
    return FileResponse("templates/admin.html")