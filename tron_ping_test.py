import asyncio
import aiohttp
import json
from db import get_config

async def ping_wallet_trc20():
    wallet = await get_config("wallet")
    if not wallet:
        print("[-] Wallet not found in database.")
        return

    print(f"[*] Checking TRC-20 transactions for wallet: {wallet}")

    url = f"https://apilist.tronscanapi.com/api/token_trc20/transfers?limit=1&sort=-timestamp&count=true&filterTokenValue=all&address={wallet}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                print(data)

                if "total" in data and data["total"] > 0 and data.get("token_transfers"):
                    tx = data["token_transfers"][0]

                    token_name = tx.get("tokenName") or tx.get("tokenInfo", {}).get("tokenName", "UNKNOWN")
                    amount = int(tx["quant"]) / 10 ** int(tx["tokenInfo"].get("tokenDecimal", 6))

                    print(f"[+] Wallet has {data['total']} TRC-20 transaction(s).")
                    print(f"    Last TX: {tx['from_address']} → {tx['to_address']}, {amount} {token_name}")
                else:
                    print("[!] No TRC-20 transactions found or invalid structure.")
    except Exception as e:
        print(f"[!] Error during request: {e}")

if __name__ == "__main__":
    asyncio.run(ping_wallet_trc20())
# not working, test file