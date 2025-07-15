from aiogram.fsm.state import StatesGroup, State

class AdminFSM(StatesGroup):
    waiting_category_name = State()
    choosing_category_to_delete = State()
    choosing_category_to_rename = State()
    renaming_category_name = State()

    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    choosing_product_category = State()
    choosing_product_stock = State()
    waiting_product_photo = State()

    choosing_product_delete_category = State()
    selecting_products_to_delete = State()

    choosing_edit_category = State()
    choosing_product_to_edit = State()
    choosing_field_to_edit = State()
    editing_field_value = State()
    editing_photo = State()

    waiting_welcome_text = State()
    waiting_group_forward = State()

    choosing_photo_category = State()
    choosing_photo_product = State()
    waiting_photo_for_product = State()

    choosing_photo_delete_category = State()
    choosing_photo_delete_product = State()
    deleting_photos = State()

    choosing_photo_view_category = State()
    choosing_photo_view_product = State()
