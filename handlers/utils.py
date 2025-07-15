from aiogram import types

def new_markup(rows: list[list[types.InlineKeyboardButton]]) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[*rows, [types.InlineKeyboardButton(text="Back", callback_data="admin_back")]]
    )

def with_back(markup: types.InlineKeyboardMarkup) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[*markup.inline_keyboard, [types.InlineKeyboardButton(text="Back", callback_data="admin_back")]]
    )
