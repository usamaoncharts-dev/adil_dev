import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def parse_symbols(value: str) -> list[str]:
    if not value:
        return []
    return [s.strip().replace(' ', '').upper().replace('/', '') for s in value.split(',') if s.strip()]


@dataclass
class Config:
    exchange_id: str = os.getenv('EXCHANGE_ID', 'binance')
    market_type: str = os.getenv('MARKET_TYPE', 'futures').lower()
    api_key: str = os.getenv('API_KEY', '')
    api_secret: str = os.getenv('API_SECRET', '')

    email_enabled: bool = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    smtp_host: str = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port: int = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    email_username: str = os.getenv('EMAIL_USERNAME', '')
    email_password: str = os.getenv('EMAIL_APP_PASSWORD', '')
    email_from: str = os.getenv('EMAIL_FROM', '')
    email_to: str = os.getenv('EMAIL_TO', '')

    symbols: list[str] = field(default_factory=lambda: parse_symbols(os.getenv('SYMBOLS', '')))
    symbols_main: list[str] = field(default_factory=lambda: parse_symbols(os.getenv('SYMBOLS_main', '')))
    timeframe: str = os.getenv('TIMEFRAME', '5m')
    fetch_limit: int = int(os.getenv('FETCH_LIMIT', '100'))
    timeframes_main: list[str] = field(default_factory=lambda: ['5m'])
    timeframes_indicators: list[str] = field(default_factory=lambda: ['15m', '1h', '4h'])
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '20'))
    request_recv_window: int = int(os.getenv('REQUEST_RECV_WINDOW', '20000'))
    max_retries: int = int(os.getenv('REQUEST_MAX_RETRIES', '3'))

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
