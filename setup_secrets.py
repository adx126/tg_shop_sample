import os
from dotenv import load_dotenv, set_key
from cryptography.fernet import Fernet
import asyncio
from db import set_config

ENV_PATH = ".env"

def ensure_env_file():
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write("")

def generate_and_save_key():
    ensure_env_file()
    load_dotenv()
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        print("[+] Encryption key already exists.")
        return key
    new_key = Fernet.generate_key().decode()
    with open(ENV_PATH, "a") as f:
        f.write(f"\nENCRYPTION_KEY={new_key}\n")
    print("[+] New encryption key generated and saved.")
    load_dotenv(override=True)
    return new_key

async def input_and_store_secrets():
    token = input("Enter Telegram bot token: ").strip()
    wallet = input("Enter crypto wallet: ").strip()
    await set_config("tgtoken", token)
    await set_config("wallet", wallet)
    print("[+] Secrets encrypted and saved to the database.")
