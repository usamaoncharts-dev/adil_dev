import logging
import time
from datetime import datetime

from bot.config import Config
from bot.exchange import BinanceDataClient
from bot.notifier import EmailNotifier
from bot.strategies.main_strategy import MainEMAStrategy
from bot.strategies.order_block_matrix_strategy import OrderBlockMatrixStrategy
from bot.strategies.smart_money_orderblock_strategy import SmartMoneyOrderBlockStrategy


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def build_strategy_instances(config: Config):
    return [
        MainEMAStrategy(config),
        OrderBlockMatrixStrategy(config),
        SmartMoneyOrderBlockStrategy(config),
    ]


def format_result(result, symbol: str, price: float) -> str:
    return (
        f'[{result.name}] {symbol} -> {result.signal.upper()} | score={result.score:.1f} | '
        f'price={price:.4f} | {result.details}'
    )


def format_email_body(result, symbol: str, price: float, timeframe: str, market_type: str) -> str:
    return (
        f'Strategy: {result.name}\n'
        f'Symbol: {symbol}\n'
        f'Timeframe: {timeframe}\n'
        f'Signal: {result.signal.upper()}\n'
        f'Score: {result.score:.1f}\n'
        f'Price: {price:.4f}\n'
        f'Timestamp (UTC): {result.timestamp.isoformat()}\n'
        '\n'
        'Details:\n'
        f'{result.details}\n'
        '\n'
        'Score explanation: internal strength value, higher is stronger, not a probability.\n'
        '\n'
        '---\n'
        f'Refresh interval: {timeframe}\n'
        f'Market type: {market_type}\n'
    )


def main():
    config = Config.load()
    client = BinanceDataClient(config)
    notifier = EmailNotifier(config)
    strategies = build_strategy_instances(config)
    strategy_timeframes = {
        'Main Strategy': config.get_timeframes_for_strategy('Main Strategy'),
        'Order Block Matrix': config.get_timeframes_for_strategy('Order Block Matrix'),
        'Smart Money Order Block': config.get_timeframes_for_strategy('Smart Money Order Block'),
    }

    logging.info('Starting Binance strategy bot')
    logging.info(f'Market type: {config.market_type}')
    logging.info(f'Main strategy symbols: {config.symbols_main}')
    logging.info(f'Other strategy symbols: {config.symbols}')

    while True:
        for strategy in strategies:
            symbols = config.get_symbols_for_strategy(strategy.name)
            timeframes = strategy_timeframes.get(strategy.name, [config.timeframe])
            for raw_symbol in symbols:
                for timeframe in timeframes:
                    try:
                        df = client.get_klines(raw_symbol, timeframe, limit=config.fetch_limit)
                        result = strategy.evaluate(df)
                        result.symbol = raw_symbol
                        result.timeframe = timeframe
                        price = client.get_live_price(raw_symbol)
                        message = format_result(result, raw_symbol, price)
                        logging.info(message)

                        if result.signal in {'buy', 'sell'}:
                            subject = (
                                f'{result.name} | {raw_symbol} | {result.signal.upper()} '
                                f'| {timeframe} | score={result.score:.1f}'
                            )
                            body = format_email_body(
                                result,
                                raw_symbol,
                                price,
                                timeframe,
                                config.market_type,
                            )
                            notifier.send(subject, body)
                    except Exception as exc:
                        logging.error(
                            f'Failed to evaluate {raw_symbol} for {strategy.name} at {timeframe}: {exc}'
                        )
        time.sleep(15)


if __name__ == '__main__':
    main()
