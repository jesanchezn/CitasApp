from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models import AvailableSlot
from app.auth import get_current_user_from_cookie
from sqlalchemy.orm import Session
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user
)
from app.database import get_db
from app.models import User, Appointment

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ------------------------------------------
# GET: Mostrar formulario de inicio de sesión
# ------------------------------------------
@router.get("/login")
def login_form(request: Request):
    message = request.query_params.get("message")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": message
    })



# ------------------------------------------
# POST: Procesar inicio de sesión con depuración
# ------------------------------------------
@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Buscar usuario por email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Correo no encontrado"
        })

    # Verificar contraseña
    if not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Contraseña incorrecta"
        })

    # Depuración
    print("🔍 Usuario encontrado:")
    print("🆔 ID:", user.id)
    print("📧 Email:", user.email)
    print("🔒 Password hash:", user.hashed_password)
    print("🛡️ Es admin:", user.is_admin)

    try:
        # Crear token
        token = create_access_token(data={"sub": str(user.id)})

        # Redirigir según rol
        redirect_url = "/admin/create-slot" if user.is_admin else "/"
        response = RedirectResponse(url=redirect_url, status_code=302)

        # Guardar token en cookie
        response.set_cookie(key="access_token", value=token, httponly=True)
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": f"Error en el servidor: {str(e)}"
        })
    
# ------------------------------------------
# POST: Registrar un usuario admin (para pruebas)
# ------------------------------------------
    
@router.post("/register-admin")
def register_admin(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"msg": "Ya existe un usuario con ese correo."}

        hashed_pw = get_password_hash(password)
        admin_user = User(
            full_name=full_name,
            username=email.split("@")[0],
            email=email,
            hashed_password=hashed_pw,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        return {"msg": "✅ Usuario admin creado exitosamente."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}



# ------------------------------------------
# GET: Mostrar formulario de registro
# ------------------------------------------
@router.get("/register")
def show_register(request: Request):
    message = request.query_params.get("message")
    return templates.TemplateResponse("register.html", {
        "request": request,
        "message": message
    })


# ------------------------------------------
# POST: Procesar formulario de registro
# ------------------------------------------
@router.post("/register")
def register_user(
    request: Request,
    db: Session = Depends(get_db),
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(
            url="/users/register?message=El+nombre+de+usuario+ya+está+en+uso", status_code=303
        )

    if db.query(User).filter(User.email == email).first():
        return RedirectResponse(
            url="/users/register?message=El+correo+electrónico+ya+está+registrado", status_code=303
        )

    hashed_password = get_password_hash(password)
    new_user = User(
        full_name=full_name,
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(
        url="/users/login?message=Registro+exitoso.+Ahora+puedes+iniciar+sesión", status_code=303
    )



# ------------------------------------------
# GET: Página principal protegida por token con depuración
# ------------------------------------------
@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    full_name = None
    user = None

    if token:
        try:
            payload = decode_access_token(token)
            print("Payload decodificado:", payload)

            user_id = payload.get("sub")
            print("ID extraído del token:", user_id)

            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                full_name = user.full_name
            else:
                print("Usuario no encontrado en la base de datos")
                return RedirectResponse(url="/login", status_code=302)
        except Exception as e:
            print("Error al decodificar token:", e)
            return RedirectResponse(url="/login", status_code=302)
    else:
        print("Token no encontrado en cookies")
        return RedirectResponse(url="/login", status_code=302)

    # 🗓️ Obtener todos los horarios disponibles
    available_slots = db.query(AvailableSlot).order_by(AvailableSlot.date, AvailableSlot.time).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "full_name": full_name,
        "available_slots": available_slots
    })


# ------------------------------------------
# GET: Cerrar sesión (borrar cookie)
# ------------------------------------------
@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/users/login?logged_out=true", status_code=302)
    response.delete_cookie("access_token")
    return response

# ------------------------------------------
# GET: Lista de usuarios (JSON)
# ------------------------------------------
@router.get("/users", tags=["Usuarios"])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ------------------------------------------
# GET: Página de "Mis citas" protegida
# ------------------------------------------
@router.get("/my_appointments")
def my_appointments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/users/login", status_code=302)

    citas = db.query(Appointment).filter(Appointment.user_id == current_user.id).all()
    return templates.TemplateResponse("my_appointments.html", {
        "request": request,
        "appointments": citas,
        "user": current_user
    })


# ------------------------------------------
# GET: Página para crear un horario disponible (solo admin)
# ------------------------------------------
@router.get("/admin/create-slot", response_class=HTMLResponse)
def admin_create_slot_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos.")
    return templates.TemplateResponse("admin_create_slot.html", {"request": request})