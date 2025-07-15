import aiosqlite

DB_PATH = "shop.db"

async def add_category(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO category (name) VALUES (?)", (name,))
        await db.commit()

async def get_all_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM category") as cursor:
            return await cursor.fetchall()

async def category_has_products(category_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM product WHERE category_id = ? LIMIT 1", (category_id,)) as cursor:
            return bool(await cursor.fetchone())

async def delete_category(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM category WHERE id = ?", (category_id,))
        await db.commit()

async def rename_category(category_id: int, new_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE category SET name = ? WHERE id = ?", (new_name, category_id))
        await db.commit()
