import sqlite3

DB_PATH = "shop.db"

def read_transactions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    rows = cursor.fetchall()

    for row in rows:
        print("-" * 40)
        print(f"ID: {row['id']}")
        print(f"TXID: {row['txid']}")
        print(f"User ID: {row['user_id']}")
        print(f"Details: {row['details']}")
    conn.close()

def temp():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id = 2")
    conn.commit()
    conn.close()

def clear():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    read_transactions()
    