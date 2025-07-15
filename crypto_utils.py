import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY not set in .env")
    return Fernet(key)

def encrypt_value(value: str) -> str:
    fernet = get_fernet()
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(encrypted: str) -> str:
    fernet = get_fernet()
    return fernet.decrypt(encrypted.encode()).decode()
