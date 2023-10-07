import ccxt
from enver import getenv
import requests

coinmarketcap_url_path = {
    'listing': getenv('COINMARKET_API_URL') + '/v1/cryptocurrency/listings/latest',
}


def find_usdt_pairs(exchange_id):
    exchange = getattr(ccxt, exchange_id)()
    markets = exchange.load_markets()
    usdt_pairs = []

    for symbol, market in markets.items():
        if 'USDT' in market['symbol']:
            usdt_pairs.append(market['symbol'])

    return {
        exchange_id: usdt_pairs
    }


def get_coinmarketcap_listing():
    url = coinmarketcap_url_path['listing']
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': getenv('COINMARKET_API_KEY'),
    }

    response = requests.get(url, params={'convert': 'USD'}, headers=headers)
    return response

