from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from services.admins import any_admins_exist, add_admin, admin_exists
from db import get_config
from keyboards.admin_panel import admin_panel_kb
from utils.message_tracker import clear_previous, track_message, track_admin_panel

# ───── FSM ─────
class AdminInit(StatesGroup):
    waiting_for_password = State()

from middlewares.check_admin import admin_only

router = Router()

# ───── /initadmin ─────
@router.message(Command("initadmin"))
async def init_admin(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)
    if await any_admins_exist():
        m = await bot.send_message(message.chat.id, "Admins already initialized.")
        track_message(message.from_user.id, m.message_id)
        return
    m = await bot.send_message(message.chat.id, "Enter the master admin password:")
    track_message(message.from_user.id, m.message_id)
    await state.set_state(AdminInit.waiting_for_password)

@router.message(AdminInit.waiting_for_password)
async def receive_password(msg: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(msg.from_user.id, bot, user_msg_id=msg.message_id)
    master_pw = await get_config("admin_password")
    if not master_pw:
        m = await bot.send_message(msg.chat.id, "Admin password not set in config.")
        track_message(msg.from_user.id, m.message_id); return
    if msg.text.strip() == master_pw.strip():
        await add_admin(msg.from_user.id)
        m = await bot.send_message(msg.chat.id, "You are now the main admin.", reply_markup=admin_panel_kb)
        track_admin_panel(msg.from_user.id, m.message_id)
    else:
        m = await bot.send_message(msg.chat.id, "Incorrect password.")
        track_message(msg.from_user.id, m.message_id)
    await state.clear()

# ───── /admin ─────
@router.message(Command("admin"))
@admin_only()
async def open_admin_panel(message: types.Message, bot: Bot):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)
    if not await admin_exists(message.from_user.id):
        m = await bot.send_message(message.chat.id, "You are not an admin.")
        track_message(message.from_user.id, m.message_id); return
    m = await bot.send_message(message.chat.id, "Admin Panel:", reply_markup=admin_panel_kb)
    track_admin_panel(message.from_user.id, m.message_id)
