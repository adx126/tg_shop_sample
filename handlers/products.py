from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from fsm.admin_states import AdminFSM
from services.products import (
    add_product, get_all_products_by_category,
    delete_products_by_ids, update_product_field,
)
from services.categories import get_all_categories
from keyboards.admin_panel import admin_panel_kb
from utils.message_tracker import clear_previous, track_message, track_admin_panel
from utils.get_delete_products_keyboard import get_delete_products_keyboard
from .utils import new_markup, with_back

from middlewares.check_admin import admin_only

router = Router()

@router.callback_query(F.data == "admin_add_product")
@admin_only()
async def start_add_product(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    categories = await get_all_categories()
    if not categories:
        sent = await bot.send_message(callback.from_user.id, "No categories available to assign product.")
        track_message(callback.from_user.id, sent.message_id)
        return

    keyboard = new_markup(
        [[types.InlineKeyboardButton(text=name, callback_data=f"addprodcat_{cat_id}")]
         for cat_id, name in categories]
    )

    sent = await bot.send_message(
        callback.from_user.id,
        "Select category for product:",
        reply_markup=keyboard,
    )
    track_message(callback.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.choosing_product_category)


@router.callback_query(F.data.startswith("addprodcat_"), AdminFSM.choosing_product_category)
@admin_only()
async def receive_product_category(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    cat_id = int(callback.data.split("_")[1])
    await state.update_data(product_category_id=cat_id)

    sent = await bot.send_message(callback.from_user.id, "Enter product name:")
    track_message(callback.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.waiting_product_name)


@router.message(AdminFSM.waiting_product_name)
@admin_only()
async def receive_product_name(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    await state.update_data(product_name=message.text.strip())

    sent = await bot.send_message(message.chat.id, "Enter product description:")
    track_message(message.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.waiting_product_description)


@router.message(AdminFSM.waiting_product_description)
@admin_only()
async def receive_product_description(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    await state.update_data(product_description=message.text.strip())

    sent = await bot.send_message(message.chat.id, "Enter product price (number):")
    track_message(message.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.waiting_product_price)


@router.message(AdminFSM.waiting_product_price)
@admin_only()
async def receive_product_price(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    try:
        price = float(message.text.strip())
    except ValueError:
        sent = await bot.send_message(message.chat.id, "Invalid number. Enter a valid price:")
        track_message(message.from_user.id, sent.message_id)
        return

    await state.update_data(product_price=price)

    sent = await bot.send_message(message.chat.id, "Should the product be in stock? (yes/no):")
    track_message(message.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.choosing_product_stock)


@router.message(AdminFSM.choosing_product_stock)
@admin_only()
async def receive_product_stock(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    stock = message.text.lower().strip() in ["yes", "true", "1", "да"]
    await state.update_data(product_stock=stock)

    sent = await bot.send_message(message.chat.id, "Send product photo:")
    track_message(message.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.waiting_product_photo)


@router.message(AdminFSM.waiting_product_photo)
@admin_only()
async def receive_product_photo(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    if not message.photo:
        sent = await bot.send_message(message.chat.id, "Please send a valid photo.")
        track_message(message.from_user.id, sent.message_id)
        return

    file_id = message.photo[-1].file_id
    data = await state.get_data()

    await add_product(
        name=data["product_name"],
        description=data["product_description"],
        price=data["product_price"],
        photo_file_id=file_id,
        category_id=data["product_category_id"],
        in_stock=data["product_stock"],
    )

    sent = await bot.send_message(
        message.chat.id,
        "Product added.",
        reply_markup=admin_panel_kb,
    )
    track_admin_panel(message.from_user.id, sent.message_id)
    await state.clear()


@router.callback_query(F.data == "admin_delete_product")
@admin_only()
async def choose_category_for_deletion(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    categories = await get_all_categories()
    if not categories:
        sent = await bot.send_message(callback.from_user.id, "No categories available.")
        track_message(callback.from_user.id, sent.message_id)
        return

    keyboard = new_markup(
        [[types.InlineKeyboardButton(text=name, callback_data=f"delprodcat_{cat_id}")]
         for cat_id, name in categories]
    )

    sent = await bot.send_message(
        callback.from_user.id,
        "Select category to delete products from:",
        reply_markup=keyboard,
    )
    track_message(callback.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.choosing_product_delete_category)


@router.callback_query(F.data.startswith("delprodcat_"), AdminFSM.choosing_product_delete_category)
@admin_only()
async def list_products_for_deletion(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    cat_id = int(callback.data.split("_")[1])
    products = await get_all_products_by_category(cat_id)

    if not products:
        sent = await bot.send_message(callback.from_user.id, "No products in this category.")
        track_message(callback.from_user.id, sent.message_id)
        return

    await state.update_data(
        delete_category_id=cat_id,
        delete_selected_ids=[],
        delete_products=products,
    )

    keyboard = with_back(get_delete_products_keyboard(products, []))

    sent = await bot.send_message(
        callback.from_user.id,
        "Select products to delete (press again to unselect):",
        reply_markup=keyboard,
    )
    track_message(callback.from_user.id, sent.message_id)
    await state.update_data(delete_message_id=sent.message_id)
    await state.set_state(AdminFSM.selecting_products_to_delete)


@router.callback_query(F.data.startswith("toggleprod_"), AdminFSM.selecting_products_to_delete)
@admin_only()
async def toggle_product(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    selected = data.get("delete_selected_ids", [])
    products = data.get("delete_products", [])
    msg_id = data.get("delete_message_id")

    prod_id = int(callback.data.split("_")[1])
    if prod_id in selected:
        selected.remove(prod_id)
    else:
        selected.append(prod_id)

    await state.update_data(delete_selected_ids=selected)

    keyboard = with_back(get_delete_products_keyboard(products, selected))

    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=msg_id,
            reply_markup=keyboard,
        )
    except Exception:
        pass

    await callback.answer(f"Selected: {len(selected)}")


@router.callback_query(F.data == "delprod_done", AdminFSM.selecting_products_to_delete)
@admin_only()
async def confirm_deletion(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    data = await state.get_data()
    selected_ids = data.get("delete_selected_ids", [])

    if selected_ids:
        await delete_products_by_ids(selected_ids)
        msg = f"Deleted {len(selected_ids)} products."
    else:
        msg = "No products selected."

    sent = await bot.send_message(
        callback.from_user.id,
        msg,
        reply_markup=admin_panel_kb,
    )
    track_admin_panel(callback.from_user.id, sent.message_id)
    await state.clear()


@router.callback_query(F.data == "admin_edit_product")
@admin_only()
async def choose_category_to_edit(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    categories = await get_all_categories()
    if not categories:
        sent = await bot.send_message(callback.from_user.id, "No categories.")
        track_message(callback.from_user.id, sent.message_id)
        return

    keyboard = new_markup(
        [[types.InlineKeyboardButton(text=name, callback_data=f"editcat_{cat_id}")]
         for cat_id, name in categories]
    )

    sent = await bot.send_message(
        callback.from_user.id,
        "Choose category:",
        reply_markup=keyboard,
    )
    track_message(callback.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.choosing_edit_category)


@router.callback_query(F.data.startswith("editcat_"), AdminFSM.choosing_edit_category)
@admin_only()
async def choose_product_to_edit(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, user_msg_id=callback.message.message_id)

    cat_id = int(callback.data.split("_")[1])
    products = await get_all_products_by_category(cat_id)

    if not products:
        sent = await bot.send_message(callback.from_user.id, "No products in this category.")
        track_message(callback.from_user.id, sent.message_id)
        return

    keyboard = new_markup(
        [[types.InlineKeyboardButton(text=p["name"], callback_data=f"editprod_{p['id']}")]
         for p in products]
    )

    sent = await bot.send_message(
        callback.from_user.id,
        "Choose product to edit:",
        reply_markup=keyboard,
    )
    track_message(callback.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.choosing_product_to_edit)


@router.callback_query(F.data.startswith("editprod_"), AdminFSM.choosing_product_to_edit)
@admin_only()
async def start_editing_product(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    prod_id = int(callback.data.split("_")[1])
    await state.update_data(edit_product_id=prod_id)

    keyboard = new_markup([
        [types.InlineKeyboardButton(text="📝 Name", callback_data="editfield_name")],
        [types.InlineKeyboardButton(text="📄 Description", callback_data="editfield_description")],
        [types.InlineKeyboardButton(text="💰 Price", callback_data="editfield_price")],
        [types.InlineKeyboardButton(text="📦 Stock", callback_data="editfield_stock")],
        [types.InlineKeyboardButton(text="🖼 Photo", callback_data="editfield_photo")],
    ])

    sent = await bot.send_message(
        callback.from_user.id,
        "Choose what to edit:",
        reply_markup=keyboard,
    )
    track_message(callback.from_user.id, sent.message_id)
    await state.set_state(AdminFSM.choosing_field_to_edit)


@router.callback_query(F.data.startswith("editfield_"), AdminFSM.choosing_field_to_edit)
@admin_only()
async def ask_new_value(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    field = callback.data.split("_")[1]
    await state.update_data(editing_field=field)

    prompts = {
        "name": "Enter new product name:",
        "description": "Enter new description:",
        "price": "Enter new price (number):",
        "stock": "In stock? (yes/no):",
        "photo": "Send new photo:",
    }

    msg = await bot.send_message(callback.from_user.id, prompts[field])
    await state.update_data(prompt_msg_id=msg.message_id)

    if field == "photo":
        await state.set_state(AdminFSM.editing_photo)
    else:
        await state.set_state(AdminFSM.editing_field_value)


@router.message(AdminFSM.editing_field_value)
@admin_only()
async def update_field_value(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await bot.delete_message(message.chat.id, prompt_msg_id)
        except Exception:
            pass

    prod_id = data["edit_product_id"]
    field = data["editing_field"]
    value = message.text.strip()

    if field == "price":
        try:
            value = float(value)
        except ValueError:
            sent = await bot.send_message(message.chat.id, "Invalid price. Try again:")
            track_message(message.from_user.id, sent.message_id)
            return
    elif field == "stock":
        value = value.lower() in ["yes", "да", "true", "1"]

    await update_product_field(prod_id, field, value)

    field_names = {
        "name": "Name",
        "description": "Description",
        "price": "Price",
        "stock": "Stock status",
        "photo": "Photo",
    }
    readable = field_names.get(field, field.capitalize())

    sent = await bot.send_message(
        message.chat.id,
        f"{readable} updated.",
        reply_markup=admin_panel_kb,
    )
    track_admin_panel(message.from_user.id, sent.message_id)
    await state.clear()


@router.message(AdminFSM.editing_photo)
@admin_only()
async def update_photo(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await bot.delete_message(message.chat.id, prompt_msg_id)
        except Exception:
            pass

    if not message.photo:
        sent = await bot.send_message(message.chat.id, "Send a valid photo.")
        track_message(message.from_user.id, sent.message_id)
        return

    file_id = message.photo[-1].file_id
    prod_id = data["edit_product_id"]

    await update_product_field(prod_id, "photo", file_id)

    sent = await bot.send_message(
        message.chat.id,
        "Photo updated.",
        reply_markup=admin_panel_kb,
    )
    track_admin_panel(message.from_user.id, sent.message_id)
    await state.clear()