from datetime import datetime
from database import Database
import ccxt
from enver import getenv
from logger import logger
import requests
from concurrent.futures import ThreadPoolExecutor

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def pump_worker():
    exchanger_data = getExchangerData()

    for exchanger_name, tickers in exchanger_data.items():
        for symbol, ticker in tickers.items():
            if (symbol.endswith('/USDT') or symbol.endswith('/USDT:USDT')) and ticker['last']:
                with Database() as db:
                    data = {
                        "exchanger_name": exchanger_name,
                        "symbol": symbol,
                        "open_interest": ticker['last'],
                        "created_at": datetime.now().strftime(DATE_FORMAT)
                    }
                    inserted_id = db.insert("coin_pumps", data)
                    db.commit()


def check_worker():
    exchanger_data = getExchangerData()

    with Database() as db:
        user_pump_settings = db.fetch_all('user_pump_settings')
        default_sec_interval = getenv('DEFAULT_PUMP_INTERVAL')
        default_perc_threshold = getenv('DEFAULT_PUMP_PERC_THRESHOLD')

        for user_pump_setting in user_pump_settings:
            if not user_pump_setting or not user_pump_setting[4]:  # is_scan check
                continue

            send_message_urls = []
            user_sec_interval = user_pump_setting[2] or default_sec_interval
            user_perc_threshold = user_pump_setting[3] or default_perc_threshold

            for exchanger_name, tickers in exchanger_data.items():
                for symbol, ticker in tickers.items():
                    if not ticker['last']:
                        continue

                    user_nearest_pump = db.fetch_nearest_pump(user_pump_setting[1], exchanger_name, symbol)
                    latest_pump = db.fetch_latest_pump(exchanger_name, symbol)

                    print('user_nearest_pump')
                    print(user_nearest_pump)

                    print('latest_pump')
                    print(latest_pump)

                    if not latest_pump or not user_nearest_pump:
                        continue

                    date_diff = latest_pump[4] - user_nearest_pump[4]
                    perc_diff = percent_difference(latest_pump[3], user_nearest_pump[3])

                    print('date_diff')
                    print(date_diff)
                    print('perc_diff')
                    print(perc_diff)

                    if date_diff.seconds >= user_sec_interval and abs(perc_diff) > user_perc_threshold:
                        db.upsert("user_last_coin_pump", "user_id", user_pump_setting[1], {
                            "exchanger_name": exchanger_name,
                            "symbol": symbol,
                            "last_pump": datetime.now().strftime(DATE_FORMAT),
                        })
                        db.commit()
                        message = gen_pnd_message(
                            exchanger_name,
                            symbol,
                            user_sec_interval,
                            user_nearest_pump[3],
                            latest_pump[3],
                            perc_diff
                        )

                        url = f"https://api.telegram.org/bot{getenv('BOT_TOKEN')}/sendMessage?chat_id={user_pump_setting[1]}&text={message}"
                        print(url)
                        send_message_urls.append(url)

            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(fetch_url, send_message_urls))

def cleaner_worker():
    with Database() as db:
        db.cursor.execute(f"""
            DELETE FROM coin_pumps
            WHERE UNIX_TIMESTAMP(NOW()) - UNIX_TIMESTAMP(created_at) > %s;
        """, (getenv('MAX_PUMP_INTERVAL'),))
        db.commit()


def getExchangerData():
    binance = ccxt.binance()
    bybit = ccxt.bybit()

    return {
        'binance': binance.fetch_tickers(),
        'bybit': bybit.fetch_tickers(),
    }


def percent_difference(old_value, new_value):
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


def gen_pnd_message(exchanger_name, symbol, interval_seconds, previous_price, last_price, price_change_percentage) -> str:
    logger.info(f"[SEND PND NOTIFICATION] Отправка уведомления для {symbol} с изменением цены на {price_change_percentage:.2f}%.")

    interval_minutes = round(interval_seconds / 60)

    """
    Отправляет уведомление пользователю о значительных изменениях в цене криптовалюты.

    :param exchange_name: Название биржи (например, Binance)
    :param interval_minutes: Интервал времени, за который произошло изменение, в минутах
    :param symbol: Символ криптовалюты (например, BTC/USD)
    :param previous_price: Предыдущая цена
    :param last_price: Последняя цена
    :param price_change_percentage: Изменение цены в процентах
    """
    return (f"📈 Изменение цены на {exchanger_name}:\n"
               f"🪙 Монета: {symbol}\n"
               f"🕒 Интервал: {interval_minutes} мин.\n"
               f"💵 Предыдущая цена: ${previous_price:.5f}\n"
               f"💰 Последняя цена: ${last_price:.5f}\n"
               f"📊 Изменение: {price_change_percentage:.2f}%")


def fetch_url(url):
    response = requests.get(url)
    return f"{url} fetched with status {response.status_code}"