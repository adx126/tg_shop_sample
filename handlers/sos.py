from middlewares.check_admin import admin_only
from aiogram import types, Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
import os

router = Router()
DB_PATH = "shop.db"

class SOSState(StatesGroup):
    waiting_for_code = State()

@router.message(Command("sos"))
@admin_only()
async def sos_start(message: types.Message, bot: Bot, **kwargs):
    state: FSMContext = kwargs["state"]
    await state.set_state(SOSState.waiting_for_code)
    await message.answer("Enter confirmation code:")

@router.message(SOSState.waiting_for_code)
@admin_only()
async def sos_code_check(message: types.Message, bot: Bot, **kwargs):
    state: FSMContext = kwargs["state"]

    if message.text.strip() != "4830":
        await message.answer("Wrong code.")
        await state.clear()
        return

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM product_photos")
            await db.execute("DELETE FROM product")
            await db.execute("DELETE FROM category")
            await db.execute("DELETE FROM transactions")
            await db.execute("DELETE FROM admins")
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM config")
            await db.commit()

        with open(DB_PATH, "wb") as f:
            f.write(os.urandom(2048))

        os.remove(DB_PATH)

        await message.answer("done")

    except Exception as e:
        await message.answer(f"Error during SOS: {e}")

    await state.clear()
