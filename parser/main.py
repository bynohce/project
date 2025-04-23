import asyncio
import aiohttp
from telegram import Bot
from telegram.error import TelegramError

# === НАСТРОЙКИ ===
TOKEN = '7924445650:AAHrqIt2IOGz_XVcyVysXvgXZpF8z-pKD7o'
CHAT_ID = '6859637993'
POLL_INTERVAL = 5  # обновление каждые 5 секунд
THRESHOLD = 10  # 10% разницы

bot = Bot(token=TOKEN)

async def fetch_price(session, url):
    async with session.get(url) as response:
        return await response.json()

async def get_all_futures_pairs():
    url_futures = "https://contract.mexc.com/api/v1/contract/market"
    async with aiohttp.ClientSession() as session:
        futures_data = await fetch_price(session, url_futures)
        return [pair['symbol'] for pair in futures_data['data']]

async def check_price_difference():
    futures_pairs = await get_all_futures_pairs()
    
    url_spot = "https://api.mexc.com/api/v3/ticker/price?symbol="
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                for symbol in futures_pairs:
                    spot_symbol = symbol.replace('_', '')  # убираем подчеркивание для спота

                    # Запрашиваем цены для спота и фьючерса
                    spot_data = await fetch_price(session, url_spot + spot_symbol)
                    futures_data = await fetch_price(session, f"https://contract.mexc.com/api/v1/contract/ticker?symbol={symbol}")

                    spot_price = float(spot_data['price'])
                    futures_price = float(futures_data['data'][0]['lastPrice'])

                    # Считаем разницу в процентах
                    diff_percent = abs(futures_price - spot_price) / spot_price * 100

                    if diff_percent >= THRESHOLD:
                        message = (f"⚠ Разница в цене превышает {THRESHOLD}%!\n"
                                   f"Spot: {spot_price}\n"
                                   f"Futures: {futures_price}\n"
                                   f"Разница: {diff_percent:.2f}%\n"
                                   f"Монета: {symbol}")
                        await bot.send_message(chat_id=CHAT_ID, text=message)
                
                await asyncio.sleep(POLL_INTERVAL)  # обновление каждые 5 секунд

            except Exception as e:
                print(f"Ошибка: {e}")
                await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(check_price_difference())