# secure_env.py
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_env_file(password: str, input_path=".env", output_path=".env.enc"):
    with open(input_path, "rb") as f:
        data = f.read()

    salt = os.urandom(16)
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(salt + encrypted)

    os.remove(input_path)
    print("[+] .env encrypted and original removed.")

def decrypt_env_file(password: str, encrypted_path=".env.enc"):
    with open(encrypted_path, "rb") as f:
        raw = f.read()

    salt, encrypted = raw[:16], raw[16:]
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted).decode()

    # Load into os.environ
    for line in decrypted.splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            os.environ[k.strip()] = v.strip()

    print("[+] .env loaded into memory.")
