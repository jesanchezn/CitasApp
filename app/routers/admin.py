from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth import get_current_user_from_cookie
from app.database import get_db
from app.models import User, Appointment, AvailableSlot
from app.schemas import SlotCreate
from app.auth import get_current_user
from app.admin_auth import verify_admin
from app.models import Reason
from app.schemas import ReasonCreate

# ============================================================
# Router de administración
# ============================================================
router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# Dependencia para verificar si el usuario es admin
# ============================================================


def verify_admin(current_user: User = Depends(get_current_user_from_cookie)):
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador.")
    return current_user


# ============================================================
# MODELOS Pydantic (para validación de entrada)
# ============================================================

class SlotCreate(BaseModel):
    """
    Modelo Pydantic para recibir datos de un horario disponible.
    """
    date: str  # Formato: YYYY-MM-DD
    time: str  # Formato: HH:MM

# ============================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================



@router.post("/create-slot", status_code=201)
def create_slot(
    slot: SlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin)
):
    """
    Crear un horario disponible para que los usuarios puedan reservar.
    Solo accesible por administradores.
    """

    # 🗓️ Convertir fecha y hora
    try:
        date_obj = datetime.strptime(slot.date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(slot.time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha u hora inválido")

    # 🔍 Verificar si el slot ya existe
    existing_slot = db.query(AvailableSlot).filter(
        AvailableSlot.date == date_obj,
        AvailableSlot.time == time_obj
    ).first()

    if existing_slot:
        raise HTTPException(status_code=400, detail="El horario ya existe")

    # ✅ Crear nuevo slot
    new_slot = AvailableSlot(date=date_obj, time=time_obj)
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)

    return {
        "message": "✅ Horario agregado correctamente",
        "slot": {
            "date": slot.date,
            "time": slot.time
        }
    }



#============================================================
# ENDPOINTS DE CONSULTA (para administración)
#============================================================   


@router.get("/slots")
def list_slots(db: Session = Depends(get_db)):
    """Obtener todos los horarios disponibles ordenados por fecha y hora."""
    slots = db.query(AvailableSlot).order_by(AvailableSlot.date, AvailableSlot.time).all()
    return [
        {"id": s.id, "date": s.date.strftime("%Y-%m-%d"), "time": s.time.strftime("%H:%M")}
        for s in slots
    ]



@router.get("/appointments")
def list_appointments(db: Session = Depends(get_db)):
    appointments = (
        db.query(Appointment)
        .join(Appointment.user)
        .outerjoin(Appointment.reason)
        .order_by(Appointment.date, Appointment.time)
        .all()
    )

    return [
        {
            "id": a.id,
            "user_name": a.user.full_name,
            "date": a.date.strftime("%Y-%m-%d"),
            "time": a.time.strftime("%H:%M"),
            "reason_name": a.reason.name if a.reason else "Sin motivo"
        }
        for a in appointments
    ]





# ============================================================
# ENDPOINTS ADICIONALES (Opcionales)
# ============================================================  

@router.delete("/delete-slot/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(get_db), user: User = Depends(verify_admin)):
    slot = db.query(AvailableSlot).filter_by(id=slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot no encontrado")
    db.delete(slot)
    db.commit()
    return {"message": "Slot eliminado correctamente"}

# ----- Obtener motivos disponibles para citas

@router.get("/reasons")
def get_reasons(db: Session = Depends(get_db), current_user: User = Depends(verify_admin)):
    reasons = db.query(Reason).all()
    return [{"id": r.id, "name": r.name} for r in reasons]


# Agregar motivo
@router.post("/add-reason")
def add_reason(reason: ReasonCreate, db: Session = Depends(get_db), user: User = Depends(verify_admin)):
    existing = db.query(Reason).filter_by(name=reason.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este motivo ya existe")

    new_reason = Reason(name=reason.name)
    db.add(new_reason)
    db.commit()
    db.refresh(new_reason)
    return {"message": "Motivo agregado", "reason": new_reason.name}

# Eliminar motivo

@router.delete("/delete-reason/{reason_id}")
def delete_reason(reason_id: int, db: Session = Depends(get_db), current_user: User = Depends(verify_admin)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")

    reason = db.query(Reason).filter(Reason.id == reason_id).first()
    if not reason:
        raise HTTPException(status_code=404, detail="Motivo no encontrado")

    db.delete(reason)
    db.commit()
    return {"message": "Motivo eliminado correctamente"}





