from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_panel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add Category", callback_data="admin_add_category"),
            InlineKeyboardButton(text="✏️ Rename Category", callback_data="admin_rename_category"),
        ],
        [
            InlineKeyboardButton(text="➖ Delete Category", callback_data="admin_delete_category"),
        ],
        [
            InlineKeyboardButton(text="📦 Add Product", callback_data="admin_add_product"),
            InlineKeyboardButton(text="🛠 Edit Product", callback_data="admin_edit_product"),
        ],
        [
            InlineKeyboardButton(text="🗑 Delete Product", callback_data="admin_delete_product"),
        ],
        [
            InlineKeyboardButton(text="💬 Edit Welcome", callback_data="admin_edit_welcome"),
        ],
        [
            InlineKeyboardButton(text="📷 Add Photo", callback_data="admin_add_photo"),
            InlineKeyboardButton(text="🗑 Del Photo", callback_data="admin_del_photo"),
        ],
        [
            InlineKeyboardButton(text="📸 See Photos", callback_data="admin_see_photos"),
        ],
    ]
)
