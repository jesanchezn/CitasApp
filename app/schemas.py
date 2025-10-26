# app/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import date, time
from typing import Optional

class UserCreate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: str

    class Config:
        orm_mode = True

class AppointmentCreate(BaseModel):
    date: str
    time: str
    reason: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    date: date
    time: str
    reason: str
    class Config:
        orm_mode = True

class SlotCreate(BaseModel):
    date: str  # formato "YYYY-MM-DD"
    time: str  # formato "HH:MM"

class ReasonCreate(BaseModel):
    name: str



