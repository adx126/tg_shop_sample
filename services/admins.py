import aiosqlite
import hashlib
import os

DB_PATH = "shop.db"

def hash_user_id(user_id: int) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()

async def admin_exists(user_id: int) -> bool:
    hashed = hash_user_id(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM admins WHERE id = ?", (hashed,)) as cursor:
            return bool(await cursor.fetchone())

async def any_admins_exist() -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM admins LIMIT 1") as cursor:
            return bool(await cursor.fetchone())

async def add_admin(user_id: int):
    hashed = hash_user_id(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO admins (id) VALUES (?)", (hashed,))
        await db.commit()