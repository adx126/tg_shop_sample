import asyncio
import os
from getpass import getpass
from secure_env import decrypt_env_file
from aiogram import Bot, Dispatcher
from db import init_db, get_config
from handlers import user, init
from services.tron_payment import fetch_new_trc20_txns
from db import set_config # use when bot started | setconfig("wallet", "yourwallethere") & look at db.py

async def run_tron_monitor():
    while True:
        try:
            await fetch_new_trc20_txns()
        except Exception as e:
            print(f"[!] TRON scanner error: {e}")
        await asyncio.sleep(30)

async def main():
    password = getpass("Enter password to unlock .env: ")
    decrypt_env_file(password)

    await init_db()
    token = await get_config("tgtoken")

    # set_config("wallet", "yourwallet") !!! only once

    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(user.router)
    dp.include_router(init.router)

    asyncio.create_task(run_tron_monitor())
    print("[✓] Tron payment scan started.")

    print("[✓] Bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
