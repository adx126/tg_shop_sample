# db.py
import aiosqlite
import asyncio

DB_PATH = "shop.db"

CREATE_TABLES_QUERY = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS admins (
    id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    desc TEXT,
    price REAL NOT NULL,
    stock BOOLEAN DEFAULT TRUE,
    category_id INTEGER REFERENCES category(id),
    photo_id TEXT
);

CREATE TABLE IF NOT EXISTS product_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    file_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    details TEXT NOT NULL
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_QUERY)
        await db.commit()

from crypto_utils import encrypt_value, decrypt_value

async def set_config(key: str, value: str):
    encrypted = encrypt_value(value)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("REPLACE INTO config (key, value) VALUES (?, ?)", (key, encrypted))
        await db.commit()

async def get_config(key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM config WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return decrypt_value(row[0]) if row else None
