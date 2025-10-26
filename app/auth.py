# =========================================================
# 📁 app/auth.py — Autenticación local + Google OAuth
# =========================================================
from datetime import datetime, timedelta
from typing import Optional
import requests

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.security import create_access_token


# =========================================================
# 🚀 CONFIGURACIÓN INICIAL
# =========================================================
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "clave_secreta_super_segura"  # ⚠️ cámbiala en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# =========================================================
# 🔐 FUNCIONES DE CONTRASEÑA
# =========================================================
def get_password_hash(password: str) -> str:
    """Devuelve el hash de una contraseña."""
    return pwd_context.hash(password[:72])  # bcrypt acepta máx. 72 caracteres


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña es válida."""
    return pwd_context.verify(plain_password, hashed_password)


# =========================================================
# 🎟️ FUNCIONES DE TOKEN JWT
# =========================================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT con expiración."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica un token JWT."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# =========================================================
# 👤 DEPENDENCIAS DE AUTENTICACIÓN
# =========================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Obtiene el usuario actual desde el encabezado Authorization."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception

    return user


def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Obtiene el usuario actual desde una cookie JWT."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token no encontrado en cookies")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


# =========================================================
# 🌐 AUTENTICACIÓN CON GOOGLE (GMAIL)
# =========================================================
GOOGLE_CLIENT_ID = "1068590230965-3d5pufjlpkhr12m77htfm8u5csuhjrho.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:8000/auth/callback"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/auth/login/google", tags=["Google"])
def login_with_google():
    """Redirige al usuario a la página de inicio de sesión de Google."""
    auth_url = (
        f"{GOOGLE_AUTH_URL}?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(auth_url)


@router.get("/auth/callback", tags=["Google"])
def google_callback(code: str, db: Session = Depends(get_db)):
    """Callback de Google: obtiene el token, crea el usuario y genera el JWT."""
    # 1️⃣ Intercambiar el código por el token
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_response = requests.post(GOOGLE_TOKEN_URL, data=data)
    token_data = token_response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Error al obtener el token de Google")

    # 2️⃣ Obtener info del usuario desde Google
    access_token = token_data["access_token"]
    user_info = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = user_info.get("email")
    full_name = user_info.get("name")

    if not email:
        raise HTTPException(status_code=400, detail="No se pudo obtener el correo de Google")

    # 3️⃣ Buscar usuario en BD o crear uno nuevo
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username=email.split("@")[0],
            full_name=full_name or "Usuario Google",
            hashed_password="",  # no necesita contraseña
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4️⃣ Crear el JWT y guardar cookie
    jwt_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(minutes=60))
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        max_age=60 * 60,
        samesite="lax"
    )

    return response
