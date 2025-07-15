from aiogram import types, Bot
from collections import defaultdict

_user_bot_messages = defaultdict(list)
_admin_panels = {}

async def clear_previous(user_id: int, bot: Bot, user_msg_id: int = None):
    if user_msg_id:
        try:
            await bot.delete_message(chat_id=user_id, message_id=user_msg_id)
        except:
            pass

    for msg_id in _user_bot_messages[user_id]:
        try:
            await bot.delete_message(chat_id=user_id, message_id=msg_id)
        except:
            pass
    _user_bot_messages[user_id].clear()

def track_message(user_id: int, msg_id: int):
    _user_bot_messages[user_id].append(msg_id)

def track_admin_panel(user_id: int, msg_id: int):
    _admin_panels[user_id] = msg_id

def is_admin_panel(msg: types.Message) -> bool:
    return _admin_panels.get(msg.from_user.id) == msg.message_id

async def edit_admin_panel_message(user_id: int, bot: Bot, text: str, reply_markup=None):
    msg_id = _admin_panels.get(user_id)
    if msg_id:
        try:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup
            )
        except:
            pass
