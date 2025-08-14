from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

# ========================
# Modelo de Usuario
# ========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)

    # Relación con citas
    appointments = relationship("Appointment", back_populates="user")


# ========================
# Modelo de Cita
# ========================
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)  # <-- TIME en vez de STRING
    reason = Column(String, nullable=True)

    # Relación con usuario
    user = relationship("User", back_populates="appointments")


# ========================
# Modelo de Horario Disponible
# ========================
class AvailableSlot(Base):
    __tablename__ = "available_slots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)  # <-- También TIME para que sea consistente

class Reason(Base):
    __tablename__ = "reasons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

