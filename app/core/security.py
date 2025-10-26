from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "20c2d836e57d88bb043e8344d5dc6e1feaa7d523ea408f8189b5ccf6f79edc90"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
