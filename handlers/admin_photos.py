from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from services.categories import get_all_categories
from services.products import get_all_products_by_category
from services.product_photos import add_photo
from fsm.admin_states import AdminFSM
from keyboards.admin_panel import admin_panel_kb
from utils.message_tracker import clear_previous, track_message, track_admin_panel
from .utils import new_markup
from services.product_photos import get_photos_by_product_id
from middlewares.check_admin import admin_only
from services.build_kb import build_delete_photos_keyboard


router = Router()

@router.callback_query(F.data == "admin_add_photo")
@admin_only()
async def choose_category(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    categories = await get_all_categories()
    if not categories:
        msg = await bot.send_message(callback.from_user.id, "No categories available.")
        track_message(callback.from_user.id, msg.message_id)
        return

    markup = new_markup([
        [types.InlineKeyboardButton(text=name, callback_data=f"addphotocat_{cat_id}")]
        for cat_id, name in categories
    ])

    msg = await bot.send_message(callback.from_user.id, "Select category:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.choosing_photo_category)


@router.callback_query(F.data.startswith("addphotocat_"), AdminFSM.choosing_photo_category)
@admin_only()
async def choose_product(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    cat_id = int(callback.data.split("_")[1])
    await state.update_data(photo_category_id=cat_id)

    products = await get_all_products_by_category(cat_id)
    if not products:
        msg = await bot.send_message(callback.from_user.id, "No products in this category.")
        track_message(callback.from_user.id, msg.message_id)
        return

    markup = new_markup([
        [types.InlineKeyboardButton(text=p["name"], callback_data=f"addphotoprod_{p['id']}")]
        for p in products
    ])

    msg = await bot.send_message(callback.from_user.id, "Select product:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.choosing_photo_product)


@router.callback_query(F.data.startswith("addphotoprod_"), AdminFSM.choosing_photo_product)
@admin_only()
async def ask_for_photo(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    prod_id = int(callback.data.split("_")[1])
    await state.update_data(photo_product_id=prod_id)

    msg = await bot.send_message(callback.from_user.id, "Send photo to attach to this product:")
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.waiting_photo_for_product)


@router.message(AdminFSM.waiting_photo_for_product)
@admin_only()
async def receive_photo(message: types.Message, bot: Bot, state: FSMContext):
    await clear_previous(message.from_user.id, bot, message.message_id)

    if not message.photo:
        msg = await bot.send_message(message.chat.id, "Please send a valid photo.")
        track_message(message.from_user.id, msg.message_id)
        return

    file_id = message.photo[-1].file_id
    data = await state.get_data()
    product_id = data["photo_product_id"]

    await add_photo(product_id, file_id)

    msg = await bot.send_message(
        message.chat.id,
        "Photo added to product.",
        reply_markup=admin_panel_kb
    )
    track_admin_panel(message.from_user.id, msg.message_id)
    await state.clear()

#--

@router.callback_query(F.data == "admin_del_photo")
@admin_only()
async def start_photo_deletion(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    categories = await get_all_categories()
    if not categories:
        msg = await bot.send_message(callback.from_user.id, "No categories available.")
        track_message(callback.from_user.id, msg.message_id)
        return

    markup = new_markup([
        [types.InlineKeyboardButton(text=name, callback_data=f"delphotocat_{cat_id}")]
        for cat_id, name in categories
    ])
    msg = await bot.send_message(callback.from_user.id, "Select category:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.choosing_photo_delete_category)

@router.callback_query(F.data.startswith("delphotocat_"), AdminFSM.choosing_photo_delete_category)
@admin_only()
async def choose_product(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    cat_id = int(callback.data.split("_")[1])
    products = await get_all_products_by_category(cat_id)

    if not products:
        msg = await bot.send_message(callback.from_user.id, "No products in this category.")
        track_message(callback.from_user.id, msg.message_id)
        return

    markup = new_markup([
        [types.InlineKeyboardButton(text=p["name"], callback_data=f"delphotoprod_{p['id']}")]
        for p in products
    ])

    msg = await bot.send_message(callback.from_user.id, "Select product:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.choosing_photo_delete_product)

@router.callback_query(F.data.startswith("delphotoprod_"), AdminFSM.choosing_photo_delete_product)
@admin_only()
async def show_photos(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    prod_id = int(callback.data.split("_")[1])
    photos = await get_photos_by_product_id(prod_id)

    if not photos:
        msg = await bot.send_message(callback.from_user.id, "No photos attached to this product.")
        track_message(callback.from_user.id, msg.message_id)
        return

    page = 0
    await state.update_data(delete_photos=photos, product_id=prod_id, selected_ids=[], page=page)

    current_photos = photos[page * 5:(page + 1) * 5]
    for idx, photo in enumerate(current_photos):
        try:
            sent = await bot.send_photo(callback.from_user.id, photo["file_id"], caption=f"{idx+1}. {photo['id']}")
            track_message(callback.from_user.id, sent.message_id)
        except Exception as e:
            print(f"[x] Failed to send photo: {e}")

    markup = await build_delete_photos_keyboard(photos, [], page)
    msg = await bot.send_message(callback.from_user.id, "Select photos to delete:", reply_markup=markup)
    await state.update_data(delete_photos_msg=msg.message_id)
    await state.set_state(AdminFSM.deleting_photos)

@router.callback_query(F.data.startswith("togglephoto_"), AdminFSM.deleting_photos)
@admin_only()
async def toggle_photo(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    photo_id = int(callback.data.split("_")[1])

    data = await state.get_data()
    selected = data["selected_ids"]
    page = data["page"]
    photos = data["delete_photos"]

    if photo_id in selected:
        selected.remove(photo_id)
    else:
        selected.append(photo_id)

    markup = await build_delete_photos_keyboard(photos, selected, page)
    try:
        await bot.edit_message_reply_markup(
            chat_id=str(callback.from_user.id),
            message_id=data["delete_photos_msg"],
            reply_markup=markup
        )
    except Exception as e:
        print(f"[x] Failed to edit reply markup: {e}")

    await state.update_data(selected_ids=selected)

@router.callback_query(F.data == "delphotoback", AdminFSM.deleting_photos)
@admin_only()
async def back_to_admin(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    msg = await bot.send_message(callback.from_user.id, "Back to panel.", reply_markup=admin_panel_kb)
    track_admin_panel(callback.from_user.id, msg.message_id)
    await state.clear()

from services.product_photos import delete_photos_by_ids

@router.callback_query(F.data == "delphotodone", AdminFSM.deleting_photos)
@admin_only()
async def delete_selected_photos(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    data = await state.get_data()
    ids = data.get("selected_ids", [])

    if ids:
        await delete_photos_by_ids(ids)
        text = f"Deleted {len(ids)} photo(s)."
    else:
        text = "No photos selected."

    msg = await bot.send_message(callback.from_user.id, text, reply_markup=admin_panel_kb)
    track_admin_panel(callback.from_user.id, msg.message_id)
    await state.clear()

@router.callback_query(F.data.startswith("photo_page_"), AdminFSM.deleting_photos)
@admin_only()
async def change_photo_page(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    data = await state.get_data()

    try:
        new_page = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        return

    photos = data["delete_photos"]
    selected = data["selected_ids"]

    await state.update_data(page=new_page)

    await clear_previous(callback.from_user.id, bot, data["delete_photos_msg"])

    current_photos = photos[new_page * 5:(new_page + 1) * 5]
    for idx, photo in enumerate(current_photos):
        try:
            file_id = photo["file_id"]
            sent = await bot.send_photo(callback.from_user.id, file_id, caption=f"{idx+1}. {photo['id']}")
            track_message(callback.from_user.id, sent.message_id)
        except Exception as e:
            print(f"[x] Failed to send photo on page {new_page}: {e}")

    markup = await build_delete_photos_keyboard(photos, selected, new_page)
    msg = await bot.send_message(callback.from_user.id, "Select photos to delete:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.update_data(delete_photos_msg=msg.message_id)

#--

@router.callback_query(F.data == "admin_see_photos")
@admin_only()
async def see_photos_choose_category(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    categories = await get_all_categories()
    if not categories:
        msg = await bot.send_message(callback.from_user.id, "No categories available.")
        track_message(callback.from_user.id, msg.message_id)
        return

    markup = new_markup([
        [types.InlineKeyboardButton(text=name, callback_data=f"seephotoscat_{cat_id}")]
        for cat_id, name in categories
    ])
    msg = await bot.send_message(callback.from_user.id, "Select category:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.choosing_photo_view_category)

@router.callback_query(F.data.startswith("seephotoscat_"), AdminFSM.choosing_photo_view_category)
@admin_only()
async def see_photos_choose_product(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    cat_id = int(callback.data.split("_")[1])
    products = await get_all_products_by_category(cat_id)

    if not products:
        msg = await bot.send_message(callback.from_user.id, "No products in this category.")
        track_message(callback.from_user.id, msg.message_id)
        return

    markup = new_markup([
        [types.InlineKeyboardButton(text=p["name"], callback_data=f"seephotosprod_{p['id']}")]
        for p in products
    ])
    msg = await bot.send_message(callback.from_user.id, "Select product:", reply_markup=markup)
    track_message(callback.from_user.id, msg.message_id)
    await state.set_state(AdminFSM.choosing_photo_view_product)

@router.callback_query(F.data.startswith("seephotosprod_"), AdminFSM.choosing_photo_view_product)
@admin_only()
async def see_product_photos(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await clear_previous(callback.from_user.id, bot, callback.message.message_id)

    try:
        product_id = int(callback.data.split("_")[1])
    except ValueError:
        msg = await bot.send_message(callback.from_user.id, "Invalid product ID.")
        track_message(callback.from_user.id, msg.message_id)
        return

    photos = await get_photos_by_product_id(product_id)

    if not photos:
        msg = await bot.send_message(callback.from_user.id, "No photos attached to this product.")
        track_message(callback.from_user.id, msg.message_id)
        return

    for photo in photos:
        decrypted_file_id = photo["file_id"]
        try:
            sent = await bot.send_photo(callback.from_user.id, decrypted_file_id)
            track_message(callback.from_user.id, sent.message_id)
        except Exception as e:
            print(f"[x] Failed to send photo {photo['id']}: {e}")

    done_msg = await bot.send_message(callback.from_user.id, "Done sending photos.", reply_markup=admin_panel_kb)
    track_admin_panel(callback.from_user.id, done_msg.message_id)
    await state.clear()
