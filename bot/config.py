import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    STREAMLIT_SECRETS = st.secrets
except Exception:
    STREAMLIT_SECRETS = {}


def get_secret(key: str, default: str = '') -> str:
    value = ''
    try:
        if STREAMLIT_SECRETS and key in STREAMLIT_SECRETS:
            value = STREAMLIT_SECRETS[key]
    except Exception:
        value = ''

    if value is None or value == '':
        value = os.getenv(key, default)

    return str(value)


def get_bool(key: str, default: bool = False) -> bool:
    val = get_secret(key, str(default))
    return str(val).strip().lower() in {'1', 'true', 'yes', 'on'}


def get_int(key: str, default: int = 0) -> int:
    try:
        return int(get_secret(key, str(default)))
    except ValueError:
        return default


def parse_symbols(value: str) -> list[str]:
    if not value:
        return []
    return [s.strip().replace(' ', '').upper().replace('/', '') for s in value.split(',') if s.strip()]


@dataclass
class Config:
    exchange_id: str = get_secret('EXCHANGE_ID', 'binance')
    market_type: str = get_secret('MARKET_TYPE', 'futures').lower()
    api_key: str = get_secret('API_KEY', '')
    api_secret: str = get_secret('API_SECRET', '')

    email_enabled: bool = get_bool('EMAIL_ENABLED', False)
    smtp_host: str = get_secret('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port: int = get_int('EMAIL_SMTP_PORT', 587)
    email_username: str = get_secret('EMAIL_USERNAME', '')
    email_password: str = get_secret('EMAIL_APP_PASSWORD', '')
    email_from: str = get_secret('EMAIL_FROM', '')
    email_to: str = get_secret('EMAIL_TO', '')

    symbols: list[str] = field(default_factory=lambda: parse_symbols(get_secret('SYMBOLS', '')))
    symbols_main: list[str] = field(default_factory=lambda: parse_symbols(get_secret('SYMBOLS_main', '')))
    timeframe: str = get_secret('TIMEFRAME', '5m')
    fetch_limit: int = get_int('FETCH_LIMIT', 100)
    timeframes_main: list[str] = field(default_factory=lambda: ['5m'])
    timeframes_indicators: list[str] = field(default_factory=lambda: ['15m', '1h', '4h'])
    request_timeout: int = get_int('REQUEST_TIMEOUT', 20)
    request_recv_window: int = get_int('REQUEST_RECV_WINDOW', 20000)
    max_retries: int = get_int('REQUEST_MAX_RETRIES', 3)

    @classmethod
    def load(cls) -> 'Config':
        return cls()

    def get_timeframes_for_strategy(self, strategy_name: str) -> list[str]:
        if strategy_name == 'Main Strategy':
            return self.timeframes_main
        return self.timeframes_indicators

    def get_symbols_for_strategy(self, strategy_name: str) -> list[str]:
        if strategy_name == 'Main Strategy' and self.symbols_main:
            return self.symbols_main
        return self.symbols or ['BTCUSDT']
