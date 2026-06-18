import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from routes import routers

app = FastAPI(title="Home Bar Platform")

static_dir = Path("static")
uploads_dir = Path("uploads")

static_dir.mkdir(parents=True, exist_ok=True)
uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

for router in routers:
    app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin/health")
def admin_health():
    return {"status": "ok"}


@app.get("/")
def serve_root():
    return FileResponse(str(static_dir / "index.html"))


@app.get("/menu")
def serve_menu():
    return FileResponse(str(static_dir / "index.html"))


@app.get("/admin")
def serve_admin():
    return FileResponse(str(static_dir / "admin" / "index.html"))


@app.get("/admin/{path:path}")
def serve_admin_spa(path: str):
    target = static_dir / "admin" / path
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    return FileResponse(str(static_dir / "admin" / "index.html"))
