import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv
from routes.contact import router as contact_router
from routes.contracts import router as contracts_router
from routes.receipts import router as receipts_router
from routes.rules import router as rules_router
from routes.batches import router as batches_router
from routes.analysis import router as analysis_router
from routes.appeals import router as appeals_router
from routes.admin_rates import router as admin_rates_router
from routes.auth import router as auth_router
from routes.documents import router as documents_router
from routes.projects import router as projects_router

load_dotenv()

app = FastAPI(
    title="ServantX API",
    description="Backend API for ServantX",
    version="1.0.0",
)

cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5000,http://localhost:3000,https://api.servantx.ai,http://localhost:5001")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

print("CORS origins: ", cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(contact_router)
app.include_router(contracts_router)
app.include_router(receipts_router)
app.include_router(rules_router)
app.include_router(batches_router)
app.include_router(analysis_router)
app.include_router(appeals_router)
app.include_router(admin_rates_router)
app.include_router(documents_router)
app.include_router(projects_router)

# Serve uploaded files
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

@app.get("/files/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve uploaded files (contracts and receipts)
    """
    full_path = uploads_dir / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(full_path)


@app.get("/")
async def root():
    return {"message": "ServantX API", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "servantx-api", "environment": os.getenv("ENVIRONMENT", "development")}



