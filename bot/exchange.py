import logging
import time

import pandas as pd
from binance.client import Client
from requests.exceptions import ConnectTimeout, ReadTimeout, RequestException, Timeout

from bot.config import Config

logger = logging.getLogger(__name__)


class BinanceDataClient:
    def __init__(self, config: Config):
        self.config = config
        request_timeout = config.request_timeout
        requests_params = {'timeout': (request_timeout, request_timeout)}
        self.client = Client(
            config.api_key,
            config.api_secret,
            requests_params=requests_params,
        )
        self.client.REQUEST_RECVWINDOW = config.request_recv_window
        self.client.REQUEST_TIMEOUT = config.request_timeout

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return symbol.replace('/', '').upper()

    def _sync_server_time(self) -> None:
        server_time = self.client.get_server_time()
        server_timestamp = int(server_time['serverTime'] / 1000)
        self.client.timestamp_offset = server_timestamp - int(time.time())

    def _request_with_retries(self, func, *args, **kwargs):
        delay = 1
        max_retries = max(1, self.config.max_retries)
        for attempt in range(1, max_retries + 1):
            try:
                self._sync_server_time()
                return func(*args, **kwargs)
            except (ConnectTimeout, ReadTimeout, Timeout, RequestException) as exc:
                if attempt >= max_retries:
                    logger.error('Request failed after %s attempts: %s', attempt, exc)
                    raise
                logger.warning(
                    'Request timeout attempt %s/%s: %s. Retrying in %s seconds...',
                    attempt,
                    max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay = min(delay * 2, 10)

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        symbol = self.normalize_symbol(symbol)
        if self.config.market_type == 'futures':
            raw = self._request_with_retries(self.client.futures_klines, symbol=symbol, interval=interval, limit=limit)
        else:
            raw = self._request_with_retries(self.client.get_klines, symbol=symbol, interval=interval, limit=limit)

        df = pd.DataFrame(raw, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignored'
        ])
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume', 'taker_buy_base_volume', 'taker_buy_quote_volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        return df

    def get_live_price(self, symbol: str) -> float:
        symbol = self.normalize_symbol(symbol)
        try:
            if self.config.market_type == 'futures':
                result = self._request_with_retries(self.client.futures_symbol_ticker, symbol=symbol)
            else:
                result = self._request_with_retries(self.client.get_symbol_ticker, symbol=symbol)
            return float(result['price'])
        except Exception:
            return float('nan')
