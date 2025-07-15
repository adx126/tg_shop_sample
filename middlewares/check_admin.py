from functools import wraps
from aiogram import types
from utils.message_tracker import track_message
from services.admins import admin_exists

def admin_only():
    def decorator(handler):
        @wraps(handler)
        async def wrapper(event, bot, *args, **kwargs):
            user_id = event.from_user.id if isinstance(event, (types.Message, types.CallbackQuery)) else None
            if not await admin_exists(user_id):
                sent = await bot.send_message(event.chat.id, "You are not an admin.")
                track_message(user_id, sent.message_id)
                return
            return await handler(event, bot, *args, **kwargs)
        return wrapper
    return decorator
