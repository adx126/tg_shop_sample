from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from fsm.admin_states import AdminFSM
from services.categories import (
    add_category, get_all_categories, delete_category,
    category_has_products, rename_category,
)
from keyboards.admin_panel import admin_panel_kb
from utils.message_tracker import clear_previous, track_message, track_admin_panel
from .utils import new_markup

from middlewares.check_admin import admin_only

router = Router()

@router.callback_query(F.data == "admin_add_category")
@admin_only()
async def start_add_category(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer(); await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)
    m = await bot.send_message(c.from_user.id, "Enter category name:")
    track_message(c.from_user.id, m.message_id)
    await state.set_state(AdminFSM.waiting_category_name)

@router.message(AdminFSM.waiting_category_name)
@admin_only()
async def receive_category_name(msg: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(msg.from_user.id, bot, user_msg_id=msg.message_id)
    name = msg.text.strip(); await add_category(name)
    m = await bot.send_message(msg.chat.id, f"Category '{name}' added.", reply_markup=admin_panel_kb)
    track_admin_panel(msg.from_user.id, m.message_id); await state.clear()

@router.callback_query(F.data == "admin_delete_category")
@admin_only()
async def choose_category_to_delete(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer(); await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)
    cats = await get_all_categories()
    if not cats:
        m = await bot.send_message(c.from_user.id, "No categories available."); track_message(c.from_user.id, m.message_id); return
    kb = new_markup([[types.InlineKeyboardButton(text=n, callback_data=f"delcat_{cid}")] for cid, n in cats])
    m = await bot.send_message(c.from_user.id, "Select category to delete:", reply_markup=kb)
    track_message(c.from_user.id, m.message_id); await state.set_state(AdminFSM.choosing_category_to_delete)

@router.callback_query(F.data.startswith("delcat_"), AdminFSM.choosing_category_to_delete)
@admin_only()
async def delete_selected_category(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer(); await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)
    cat_id = int(c.data.split("_")[1])
    if await category_has_products(cat_id):
        m = await bot.send_message(c.from_user.id, "Cannot delete: category has products.", reply_markup=admin_panel_kb)
        track_admin_panel(c.from_user.id, m.message_id); await state.clear(); return
    await delete_category(cat_id)
    m = await bot.send_message(c.from_user.id, "Category deleted.", reply_markup=admin_panel_kb)
    track_admin_panel(c.from_user.id, m.message_id); await state.clear()

@router.callback_query(F.data == "admin_rename_category")
@admin_only()
async def choose_category_to_rename(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer(); await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)
    cats = await get_all_categories()
    if not cats:
        m = await bot.send_message(c.from_user.id, "No categories to rename."); track_message(c.from_user.id, m.message_id); return
    kb = new_markup([[types.InlineKeyboardButton(text=n, callback_data=f"renamecat_{cid}")] for cid, n in cats])
    m = await bot.send_message(c.from_user.id, "Select category to rename:", reply_markup=kb)
    track_message(c.from_user.id, m.message_id); await state.set_state(AdminFSM.choosing_category_to_rename)

@router.callback_query(F.data.startswith("renamecat_"), AdminFSM.choosing_category_to_rename)
@admin_only()
async def request_new_category_name(c: types.CallbackQuery, bot: Bot, state: FSMContext):
    await c.answer(); await clear_previous(c.from_user.id, bot, user_msg_id=c.message.message_id)
    await state.update_data(category_id=int(c.data.split("_")[1]))
    m = await bot.send_message(c.from_user.id, "Enter new category name:")
    track_message(c.from_user.id, m.message_id); await state.set_state(AdminFSM.renaming_category_name)

@router.message(AdminFSM.renaming_category_name)
@admin_only()
async def receive_new_category_name(msg: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(msg.from_user.id, bot, user_msg_id=msg.message_id)
    cat_id = (await state.get_data())["category_id"]; new_name = msg.text.strip()
    await rename_category(cat_id, new_name)
    m = await bot.send_message(msg.chat.id, f"Category renamed to '{new_name}'.", reply_markup=admin_panel_kb)
    track_admin_panel(msg.from_user.id, m.message_id); await state.clear()
