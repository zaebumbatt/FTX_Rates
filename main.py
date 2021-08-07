import hmac
import os
import time

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

old_rates = {
    "USD": 0,
    "USDT": 0
}


def get_latest_rates():
    response = s.send(prepared)

    if response.status_code == 200:
        for result in response.json()["result"]:
            coin = result['coin']
            if coin in old_rates:
                new_rate = float(result['estimate']) * 24 * 365 * 100
                old_rate = old_rates.get(coin)

                if abs(old_rate - new_rate) > 0.5:
                    send_message(create_message(coin, old_rate, new_rate))
                    old_rates[coin] = new_rate


def create_message(coin, old_rate, new_rate):
    return f"Coin: {coin}\nLast updated rate: {old_rate:.2f}\nNew estimated rate: {new_rate:.2f}"


def send_message(message):
    return BOT.send_message(chat_id=CHAT_ID, text=message)


if __name__ == "__main__":
    while True:
        time.sleep(10)
        get_latest_rates()
