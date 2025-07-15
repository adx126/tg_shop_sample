# services/products.py
import aiosqlite

DB_PATH = "shop.db"

async def get_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM category") as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[0], "name": row[1]} for row in rows]

async def get_products_by_category(category_id: int, page: int = 0):
    offset = page * 5
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT id, name, price FROM product
            WHERE category_id = ? AND stock = TRUE
            LIMIT 5 OFFSET ?
        """
        async with db.execute(query, (category_id, offset)) as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]

async def get_product_by_id(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT name, desc, price, photo_id FROM product WHERE id = ?"
        async with db.execute(query, (product_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "desc": row[1],
                    "price": row[2],
                    "photo_id": row[3]
                }

async def add_product(name: str, description: str, price: float, photo_file_id: str, category_id: int, in_stock: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            INSERT INTO product (name, desc, price, photo_id, category_id, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        await db.execute(query, (name, description, price, photo_file_id, category_id, int(in_stock)))
        await db.commit()

async def get_all_products_by_category(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT id, name, price, stock FROM product
            WHERE category_id = ?
        """
        async with db.execute(query, (category_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "price": row[2],
                    "stock": row[3]
                }
                for row in rows
            ]

async def delete_products_by_ids(ids: list[int]):
    if not ids:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany("DELETE FROM product WHERE id = ?", [(i,) for i in ids])
        await db.commit()

async def update_product_field(product_id: int, field: str, value):
    field_map = {
        "name": "name",
        "description": "desc",
        "price": "price",
        "stock": "stock",
        "photo": "photo_id"
    }

    db_field = field_map.get(field)
    if db_field is None:
        raise ValueError("Invalid field")

    query = f"UPDATE product SET {db_field} = ? WHERE id = ?"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, (value, product_id))
        await db.commit()
