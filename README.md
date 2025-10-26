# 🩺 CitasApp – Sistema de Reservas de Citas

Aplicación desarrollada con **FastAPI** para gestionar el registro y reserva de citas.  
Incluye autenticación con JWT, manejo de base de datos, y un panel administrativo para gestión de usuarios y citas.

---

## 🚀 Requisitos previos

Asegúrate de tener instalado:

- 🐍 **Python 3.8+**
- 💻 **Git**
- 🐘 **PostgreSQL 18+**
- 🧠 (Opcional) **pgAdmin** para gestión visual de la base de datos
- ⚙️ (Opcional) **Git Bash o PowerShell** en Windows

---


### 1️⃣ Clonar el repositorio

git clone https://github.com/jesanchezn/CitasApp.git
cd CitasApp

## 2️⃣ Crear entorno virtual

python -m venv venv


## 3️⃣ Activar entorno virtual

source venv/Scripts/activate

- En CMD o PowerShell:
.\venv\Scripts\activate

## Instalación de dependencias

pip install -r requirements.txt

##  🛠️ Configuración de la base de datos (PostgreSQL)

Este proyecto fue migrado de SQLite a PostgreSQL para mayor robustez.
🔧 Pasos para configurar PostgreSQL
- Instala PostgreSQL 18 desde https://www.postgresql.org/download/
- Crea una base de datos llamada citas_db
- Asigna una contraseña al usuario postgres (o crea un usuario personalizado)
- Actualiza la URL de conexión en app/database.py:

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:tu_contraseña@localhost:5432/citas_db"

## 🧱 Inicializar tablas

Ejecuta el siguiente comando desde la raíz del proyecto:

python -m app.init_db


## 🚀 Ejecución del servidor FastAPI

uvicorn app.main:app --reload


## Accede a la documentación interactiva en:

https://localhost:8000/docs


```bash
