from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Appointment, AvailableSlot, User, Reason
from app.auth import get_current_user_from_cookie

router = APIRouter()

# 📦 SCHEMAS
class SlotCreate(BaseModel):
    date: str  # formato YYYY-MM-DD
    time: str  # formato HH:MM

class AppointmentCreate(BaseModel):
    date: str
    time: str
    reason: Optional[str] = None  # 👈 motivo de la cita

# 1️⃣ ADMIN — Agregar un horario disponible
@router.post("/add-slot")
def add_available_slot(slot: SlotCreate, db: Session = Depends(get_db)):
    try:
        date_obj = datetime.strptime(slot.date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(slot.time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha u hora inválido")

    new_slot = AvailableSlot(date=date_obj, time=time_obj)
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)

    return {
        "message": "Horario agregado",
        "slot": {"date": slot.date, "time": slot.time}
    }

# 2️⃣ Usuario — Obtener horarios libres para una fecha
@router.get("/available")
def get_available_slots(date: str, db: Session = Depends(get_db)):
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")

    horarios_disponibles = (
        db.query(AvailableSlot)
        .filter(AvailableSlot.date == date_obj)
        .order_by(AvailableSlot.time)
        .all()
    )

    citas_ocupadas = (
        db.query(Appointment.time)
        .filter(Appointment.date == date_obj)
        .all()
    )
    horas_ocupadas = {c[0].strftime("%H:%M") for c in citas_ocupadas}

    horas_libres = [
        slot.time.strftime("%H:%M")
        for slot in horarios_disponibles
        if slot.time.strftime("%H:%M") not in horas_ocupadas
    ]

    return horas_libres

# 3️⃣ Usuario — Crear una cita (usando token)
@router.post("/create")
def create_appointment(
    appt: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    try:
        date_obj = datetime.strptime(appt.date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(appt.time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha u hora inválido")

    # Verificar si ya existe una cita en esa hora
    cita_existente = db.query(Appointment).filter(
        Appointment.date == date_obj,
        Appointment.time == time_obj
    ).first()

    if cita_existente:
        return {"error": "Horario no disponible"}

    # Buscar el motivo (por id)
    reason_obj = None
    if appt.reason:  # 👈 Si viene el motivo, lo buscamos por ID o por nombre
        reason_obj = db.query(Reason).filter(
            (Reason.id == appt.reason) | (Reason.name == appt.reason)
        ).first()
        if not reason_obj:
            raise HTTPException(status_code=404, detail="Motivo no encontrado")

    # Crear la cita con el ID del motivo
    nueva_cita = Appointment(
        date=date_obj,
        time=time_obj,
        user_id=current_user.id,
        reason_id=reason_obj.id if reason_obj else None
    )

    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    return {
        "message": "Cita creada correctamente",
        "appointment": {
            "date": appt.date,
            "time": appt.time,
            "reason": reason_obj.name if reason_obj else "Sin motivo",
            "user": current_user.full_name
        }
    }



@router.post("/cancel/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    cita = db.query(Appointment).filter_by(id=appointment_id, user_id=current_user.id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    db.delete(cita)
    db.commit()

    return {"message": "Cita cancelada correctamente"}