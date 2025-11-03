import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from decouple import config

async def send_email(to_email: str, subject: str, body: str):
    sender_email = config("GMAIL_USER")
    sender_name = "Sistema de Citas"
    password = config("GMAIL_PASS")

    # 📦 Crear el mensaje
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = to_email
    msg["Subject"] = subject

    # Cuerpo del correo (HTML)
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        # Conexión segura con Gmail
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            print(f"📨 Correo enviado correctamente a {to_email}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
