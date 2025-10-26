from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.database import engine, Base
from app.routers import users, appointments, admin, public  # ← incluye el router público
from app.admin_auth import admin_required  # Middleware para validar admin
from app import auth

import logging
logging.basicConfig(level=logging.DEBUG)

# --------------------------------------------------
# Inicializar la aplicación
# --------------------------------------------------
app = FastAPI(title="Sistema de Reservas de Citas")

# --------------------------------------------------
# Archivos estáticos y templates
# --------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------
# Crear tablas en la base de datos
# --------------------------------------------------
Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# Registrar routers
# --------------------------------------------------
app.include_router(users.router, prefix="/users", tags=["Usuarios"])
app.include_router(appointments.router, prefix="/appointments", tags=["Citas"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(public.router, tags=["Público"])  # ← acceso a motivos para usuarios
app.include_router(auth.router)

# --------------------------------------------------
# Rutas principales
# --------------------------------------------------
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/users/")

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/admin/create-slot", response_class=HTMLResponse)
def admin_page(request: Request, current_user=Depends(admin_required)):
    return templates.TemplateResponse("admin_create_slot.html", {"request": request})