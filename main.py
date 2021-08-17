import hmac
import os
import time
from datetime import datetime

import telegram
from dotenv import load_dotenv
from requests import Request, Session

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BOT = telegram.Bot(token=TELEGRAM_TOKEN)

ts = int(time.time() * 1000)
request = Request('GET', 'https://ftx.com/api/spot_margin/lending_rates')
prepared = request.prepare()
signature_payload = f'{ts}{prepared.method}{prepared.path_url}'
if prepared.body:
    signature_payload += prepared.body
signature_payload = signature_payload.encode()
signature = hmac.new(os.getenv("FTX_API_SECRET").encode(), signature_payload, 'sha256').hexdigest()

prepared.headers['FTX-KEY'] = os.getenv("FTX_API_KEY")
prepared.headers['FTX-SIGN'] = signature
prepared.headers['FTX-TS'] = str(ts)

s = Session()
COINS = ("USD", "USDT", "BTC", "ETH")


def get_latest_rates():
    response = s.send(prepared)

    if response.status_code == 200:
        rates = {}
        for result in response.json()["result"]:
            coin = result['coin']
            if coin in COINS:
                rates[coin] = float(result['previous']) * 24 * 365 * 100

        message = [
            f"Coin: {coin}\nRate for previous hour: {rate:.2f}\n\n"
            for coin, rate in rates.items()
        ]
        send_message("".join(message))


def send_message(message):
    return BOT.send_message(chat_id=CHAT_ID, text=message)


if __name__ == "__main__":
    while True:
        if datetime.now().minute == 1:
            get_latest_rates()
            time.sleep(61)
