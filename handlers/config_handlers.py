from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext

from fsm.admin_states import AdminFSM
from db import set_config
from keyboards.admin_panel import admin_panel_kb
from utils.message_tracker import clear_previous, track_message, track_admin_panel
from services.admins import admin_exists
from aiogram.filters import Command

from middlewares.check_admin import admin_only

router = Router()


# ────────── EDIT WELCOME ──────────
@router.callback_query(F.data == "admin_edit_welcome")
@admin_only()
async def start_edit_welcome(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer()
    await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)

    m = await bot.send_message(c.from_user.id, "Send new *welcome-message* text:")
    track_message(c.from_user.id, m.message_id)
    await state.set_state(AdminFSM.waiting_welcome_text)


@router.message(AdminFSM.waiting_welcome_text)
@admin_only()
async def save_welcome(msg: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(msg.from_user.id, bot, user_msg_id=msg.message_id)

    text = msg.text.strip()
    await set_config("welcome_message", text)

    m = await bot.send_message(msg.chat.id, "Welcome-message updated.", reply_markup=admin_panel_kb)
    track_admin_panel(msg.from_user.id, m.message_id)
    await state.clear()


# ────────── CHANGE GROUP ──────────
@router.message(Command("maingroup"))
@admin_only()
async def set_main_group(message: types.Message, bot: Bot, state: FSMContext):
    
    if not await admin_exists(message.from_user.id):
        sent = await bot.send_message(message.chat.id, "You are not an admin.")
        track_message(message.from_user.id, sent.message_id)
        return

    if message.chat.type not in {"group", "supergroup"}:
        sent = await bot.send_message(
            message.chat.id,
            "This command must be used *in the group* you want to set as main.",
        )
        track_message(message.from_user.id, sent.message_id)
        return

    await set_config("group_id", str(message.chat.id))

    sent = await bot.send_message(
        message.chat.id,
        f"Group ID `{message.chat.id}` saved to config.",
    )