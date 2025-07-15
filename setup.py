import asyncio
from setup_secrets import generate_and_save_key, input_and_store_secrets
from db import init_db, set_config
from getpass import getpass
from secure_env import encrypt_env_file

async def full_setup():
    print("[*] Initializing database...")
    await init_db()
    print("[+] Database initialized.")

    print("[*] Creating .env and writing encryption key...")
    generate_and_save_key()

    print("[*] Storing secrets (bot token, wallet)...")
    await input_and_store_secrets()

    admin_pw = getpass("Set master admin password: ").strip()
    if not admin_pw or len(admin_pw) < 6:
        print("[-] Password too short, must be at least 6 characters.")
        return
    await set_config("admin_password", admin_pw)
    print("[+] Master admin password saved.")

    password = getpass("Set a password to protect your .env: ")
    encrypt_env_file(password)

    print("[✓] Setup complete and .env encrypted.")

if __name__ == "__main__":
    asyncio.run(full_setup())
