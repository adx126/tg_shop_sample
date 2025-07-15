from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_delete_products_keyboard(products: list, selected_ids: list):
    buttons = []
    for p in products:
        selected = "🗑️" if p["id"] in selected_ids else ""
        btn = InlineKeyboardButton(
            text=f"{selected} {p['name']} – {p['price']} USDT",
            callback_data=f"toggleprod_{p['id']}"
        )
        buttons.append([btn])

    buttons.append([InlineKeyboardButton(text="Done", callback_data="delprod_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
