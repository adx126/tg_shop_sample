from aiogram import Router, Bot, types, F
from aiogram.filters import CommandStart
from db import get_config
from services.products import get_categories, get_products_by_category, get_product_by_id
from utils.message_tracker import track_message, clear_previous
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.tron_payment import link_txid_to_user
from services.product_photos import get_and_delete_random_photo

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message, bot: Bot):
    await clear_previous(message.from_user.id, bot, user_msg_id=message.message_id)

    welcome = await get_config("welcome_message") or "Welcome"
    categories = await get_categories()

    if not categories:
        sent = await message.answer("No categories available.")
        track_message(message.from_user.id, sent.message_id)
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=cat["name"], callback_data=f"cat_{cat['id']}")]
            for cat in categories
        ]
    )

    sent = await message.answer(welcome, reply_markup=keyboard)
    track_message(message.from_user.id, sent.message_id)

@router.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id

    cat_id = int(callback.data.split("_")[1])
    await state.update_data(current_page=0, current_category=cat_id)

    products = await get_products_by_category(cat_id, page=0)
    if not products:
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=callback.message.message_id,
            text="No products in this category."
        )
        return

    # Проверим, есть ли товары на следующей странице
    next_page_products = await get_products_by_category(cat_id, page=1)

    nav_buttons = []
    if next_page_products:
        nav_buttons.append(types.InlineKeyboardButton(text="»", callback_data=f"page_{cat_id}_next"))

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            *[[types.InlineKeyboardButton(
                text=f"{p['name']} – {p['price']} USDT",
                callback_data=f"prod_{p['id']}_{cat_id}"
            )] for p in products],
            *([nav_buttons] if nav_buttons else []),
            [types.InlineKeyboardButton(text="← Back to categories", callback_data="back_to_categories")]
        ]
    )

    await bot.send_message(user_id, "Available products:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("page_"))
async def switch_page(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id

    try:
        _, cat_id, direction = callback.data.split("_")
        cat_id = int(cat_id)
    except Exception:
        await bot.send_message(user_id, "Invalid page format.")
        return

    data = await state.get_data()
    current_page = data.get("current_page", 0)
    current_category = data.get("current_category", cat_id)

    if current_category != cat_id:
        current_page = 0

    new_page = current_page + 1 if direction == "next" else max(0, current_page - 1)

    products = await get_products_by_category(cat_id, page=new_page)
    if not products:
        await callback.answer("No more products.", show_alert=True)
        return

    await state.update_data(current_page=new_page, current_category=cat_id)

    next_page_products = await get_products_by_category(cat_id, page=new_page + 1)

    nav_buttons = []
    if new_page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="«", callback_data=f"page_{cat_id}_prev"))
    if next_page_products:
        nav_buttons.append(types.InlineKeyboardButton(text="»", callback_data=f"page_{cat_id}_next"))

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            *[[types.InlineKeyboardButton(
                text=f"{p['name']} – {p['price']} USDT",
                callback_data=f"prod_{p['id']}_{cat_id}"
            )] for p in products],
            *([nav_buttons] if nav_buttons else []),
            [types.InlineKeyboardButton(text="← Back to categories", callback_data="back_to_categories")]
        ]
    )

    await bot.edit_message_text(
        chat_id=user_id,
        message_id=callback.message.message_id,
        text="Available products:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    await clear_previous(user_id, bot, user_msg_id=callback.message.message_id)
    await start_handler(callback.message, bot)


@router.callback_query(F.data.startswith("prod_"))
async def product_selected(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    await clear_previous(user_id, bot, user_msg_id=callback.message.message_id)

    prod_id, cat_id = map(int, callback.data.split("_")[1:3])
    product = await get_product_by_id(prod_id)

    if not product:
        sent = await bot.send_message(user_id, "Product not found.")
        track_message(user_id, sent.message_id)
        return

    caption = f"<b>{product['name']}</b>\n\n{product['desc']}\n\nPrice: {product['price']} USDT"
    buttons = [
        [types.InlineKeyboardButton(text="Buy", callback_data=f"buy_{prod_id}_{cat_id}")],
        [types.InlineKeyboardButton(text="Back", callback_data=f"cat_{cat_id}")]
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    if product["photo_id"]:
        sent = await bot.send_photo(
            chat_id=user_id,
            photo=product["photo_id"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=markup
        )
    else:
        sent = await bot.send_message(
            chat_id=user_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=markup
        )

    track_message(user_id, sent.message_id)

#--

@router.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    await clear_previous(user_id, bot, user_msg_id=callback.message.message_id)

    prod_id, cat_id = map(int, callback.data.split("_")[1:3])
    product = await get_product_by_id(prod_id)
    if not product:
        sent = await bot.send_message(user_id, "Product not found.")
        track_message(user_id, sent.message_id)
        return

    tron_wallet = await get_config("wallet") or "TRON_WALLET_NOT_SET"
    price = product["price"]

    message = (
            f"To complete your purchase, send exactly <b>{price} USDT</b> (TRC-20) to the wallet address:\n\n"
            f"<code>{tron_wallet}</code>\n\n"
            "After the transaction is complete, press <b>Done</b> and submit the transaction hash (txid)."
    )

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Done", callback_data=f"txid_{prod_id}")],
            [types.InlineKeyboardButton(text="Back", callback_data=f"prod_{prod_id}_{cat_id}")]
        ]
    )

    sent = await bot.send_message(
        chat_id=user_id,
        text=message,
        parse_mode="HTML",
        reply_markup=markup
    )
    track_message(user_id, sent.message_id)

class TxidFSM(StatesGroup):
    waiting_for_txid = State()

@router.callback_query(F.data.startswith("txid_"))
async def ask_for_txid(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    await clear_previous(user_id, callback.bot, user_msg_id=callback.message.message_id)

    prod_id = int(callback.data.split("_")[1])
    await state.update_data(prod_id=prod_id)

    sent = await callback.message.answer("Please send the transaction hash (txid):")
    track_message(user_id, sent.message_id)
    await state.set_state(TxidFSM.waiting_for_txid)

@router.message(TxidFSM.waiting_for_txid)
async def process_txid(message: types.Message, state: FSMContext, bot: Bot):
    txid = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    data = await state.get_data()
    prod_id = data.get("prod_id")
    await clear_previous(user_id, bot, user_msg_id=message.message_id)

    if not prod_id:
        await message.answer("Something went wrong.")
        return

    success = await link_txid_to_user(txid, user_id)
    if not success:
        await message.answer("Transaction not found or already linked.")
        return

    photo_file_id = await get_and_delete_random_photo(prod_id)
    if photo_file_id:
        await bot.send_photo(
            chat_id=user_id,
            photo=photo_file_id,
            caption="Purchase successful!",
        )
    else:
        await message.answer("Purchase successful!")

    group_id = await get_config("group_id")
    if group_id:
        caption = (
            f"🧾 <b>New Purchase</b>\n\n"
            f"<b>User:</b> <code>{user_id}</code> ({username})\n"
            f"<b>TXID:</b> <code>{txid}</code>\n"
            f"<b>Product ID:</b> {prod_id}"
        )
        try:
            if photo_file_id:
                await bot.send_photo(chat_id=int(group_id), photo=photo_file_id, caption=caption, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=int(group_id), text=caption, parse_mode="HTML")
        except Exception as e:
            print(f"[!] Failed to send group notification: {e}")

    await state.clear()