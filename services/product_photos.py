from db import DB_PATH
from crypto_utils import encrypt_value, decrypt_value
import aiosqlite
import random

async def add_photo(product_id: int, file_id: str):
    encrypted = encrypt_value(file_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO product_photos (product_id, file_id) VALUES (?, ?)",
            (product_id, encrypted)
        )
        await db.commit()

async def get_photos_by_product_id(product_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id, id FROM product_photos WHERE product_id = ?", (product_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[1], "file_id": decrypt_value(row[0])} for row in rows]

async def get_and_delete_random_photo(product_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, file_id FROM product_photos WHERE product_id = ?", (product_id,)
        ) as cursor:
            rows = await cursor.fetchall()

        if not rows:
            return None

        selected = random.choice(rows)
        photo_id_db, encrypted_file_id = selected
        file_id = decrypt_value(encrypted_file_id)

        await db.execute("DELETE FROM product_photos WHERE id = ?", (photo_id_db,))
        await db.commit()

        return file_id

async def delete_photos_by_ids(photo_ids: list[int]):
    if not photo_ids:
        return

    placeholders = ",".join(["?"] * len(photo_ids))
    query = f"DELETE FROM product_photos WHERE id IN ({placeholders})"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, photo_ids)
        await db.commit()

async def has_photos(product_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM product_photos WHERE product_id = ? LIMIT 1", (product_id,)
        ) as cursor:
            return await cursor.fetchone() is not None
