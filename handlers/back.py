from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from keyboards.admin_panel import admin_panel_kb
from utils.message_tracker import clear_previous, track_admin_panel

from middlewares.check_admin import admin_only

router = Router()

@router.callback_query(F.data == "admin_back")
@admin_only()
async def go_back_admin(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer()
    await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)
    m = await bot.send_message(c.from_user.id, "Admin Panel:", reply_markup=admin_panel_kb)
    track_admin_panel(c.from_user.id, m.message_id)
    await state.clear()
