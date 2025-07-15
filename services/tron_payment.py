import httpx
import aiosqlite
from db import get_config
import hashlib

def deterministic_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

async def fetch_new_trc20_txns():
    tron_address = await get_config("wallet")
    if not tron_address:
        print("[!] TRON wallet not set in config.")
        return

    url = (
        f"https://apilist.tronscanapi.com/api/new/token_trc20/transfers"
        f"?sort=-timestamp&count=true&limit=50&start=0&toAddress={tron_address}"
    )

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
        except Exception as e:
            print(f"[!] Failed to fetch TRON data: {e}")
            return

        data = r.json()
        tx_list = data.get("token_transfers", [])

        async with aiosqlite.connect("shop.db") as db:
            for tx in tx_list:
                if tx.get("tokenInfo", {}).get("tokenAbbr") != "USDT":
                    continue

                txid = tx.get("transaction_id")
                if not txid:
                    continue

                encrypted_txid = deterministic_hash(txid)

                async with db.execute("SELECT 1 FROM transactions WHERE txid = ?", (encrypted_txid,)) as cursor:
                    if await cursor.fetchone():
                        continue

                amount = str(int(tx.get("quant")) / (10 ** tx["tokenInfo"].get("tokenDecimal", 6)))
                sender = tx.get("from_address")
                receiver = tx.get("to_address")

                if not (amount and sender and receiver):
                    continue

                details = {
                    "from": sender,
                    "to": receiver,
                    "amount": amount
                }

                encrypted_details = deterministic_hash(str(details))
                zero_user = deterministic_hash("0")

                try:
                    await db.execute("""
                        INSERT INTO transactions (txid, user_id, details)
                        VALUES (?, ?, ?)
                    """, (encrypted_txid, zero_user, encrypted_details))
                    await db.commit()
                    print(f"[+] New USDT TX: {txid}")
                except aiosqlite.IntegrityError:
                    continue

async def link_txid_to_user(txid: str, user_id: int) -> bool:
    encrypted_txid = deterministic_hash(txid)
    zero_user = deterministic_hash("0")

    async with aiosqlite.connect("shop.db") as db:
        async with db.execute(
            "SELECT id, details FROM transactions WHERE txid = ? AND user_id = ?",
            (encrypted_txid, zero_user)
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            return False

        tx_db_id = row[0]
        old_details = row[1]

        encrypted_user_id = deterministic_hash(str(user_id))
        encrypted_details = deterministic_hash(old_details)

        await db.execute("""
            UPDATE transactions
            SET user_id = ?, details = ?
            WHERE id = ?
        """, (encrypted_user_id, encrypted_details, tx_db_id))

        await db.commit()
        return True

