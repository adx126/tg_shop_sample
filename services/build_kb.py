import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def build_delete_photos_keyboard(photos, selected_ids, page=0, per_page=5):
    start = page * per_page
    end = start + per_page
    current_photos = photos[start:end]

    buttons = []
    for idx, photo in enumerate(current_photos):
        photo_id = photo["id"]
        number = idx + start + 1
        text = f"🗑 {number} ({photo_id})" if photo_id in selected_ids else f"{number} ({photo_id})"
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"togglephoto_{photo_id}"))


    rows = [buttons[i:i+5] for i in range(0, len(buttons), 5)]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)

    # Пагинация
    total_pages = math.ceil(len(photos) / per_page)
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(text="<", callback_data=f"photo_page_{page - 1}"))

        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(text=">", callback_data=f"photo_page_{page + 1}"))
        markup.inline_keyboard.append(pagination)

    # Контрольные кнопки
    markup.inline_keyboard.append([
        InlineKeyboardButton(text="Back", callback_data="delphotoback"),
        InlineKeyboardButton(text="Done", callback_data="delphotodone")
    ])

    return markup