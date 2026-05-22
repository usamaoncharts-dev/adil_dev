import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bot.config import Config
from bot.exchange import BinanceDataClient
from bot.strategies.main_strategy import MainEMAStrategy
from bot.strategies.order_block_matrix_strategy import OrderBlockMatrixStrategy
from bot.strategies.smart_money_orderblock_strategy import SmartMoneyOrderBlockStrategy


@st.cache_data(ttl=30)
def load_klines(_client: BinanceDataClient, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    return _client.get_klines(symbol, timeframe, limit=limit)


def format_result(result, symbol: str, price: float) -> str:
    return (
        f'{result.name} | {symbol} | {result.signal.upper()} | score={result.score:.1f}\n'
        f'price={price:.4f}\n{result.details}'
    )


def render_strategy_page(strategy, symbols, client, config):
    st.header(strategy.name)
    st.write(strategy.description)
    st.write('Symbols monitored:', ', '.join(symbols))

    timeframes = config.get_timeframes_for_strategy(strategy.name)
    symbol_results = []
    errors = []

    for raw_symbol in symbols:
        price = client.get_live_price(raw_symbol)
        display_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        strategy_results = []
        for timeframe in timeframes:
            try:
                df = load_klines(client, raw_symbol, timeframe, limit=config.fetch_limit)
                result = strategy.evaluate(df)
                result.symbol = raw_symbol
                result.timeframe = timeframe
                result.price = price
                result.df = df
                result.display_time = display_time
                strategy_results.append(result)
            except Exception as exc:
                errors.append((raw_symbol, timeframe, exc))

        if strategy_results:
            symbol_results.append((raw_symbol, strategy_results))

    active_symbols = [
        (symbol, results)
        for symbol, results in symbol_results
        if any(r.signal in {'buy', 'sell'} for r in results)
    ]
    neutral_symbols = [
        (symbol, results)
        for symbol, results in symbol_results
        if not any(r.signal in {'buy', 'sell'} for r in results)
    ]

    if active_symbols:
        st.subheader('Active Signals')
        for symbol, results in active_symbols:
            with st.expander(f'{symbol} — active signal', expanded=True):
                for result in results:
                    if result.signal in {'buy', 'sell'}:
                        if result.signal == 'buy':
                            st.success(f'**{symbol}** | {result.signal.upper()} | {result.timeframe}')
                        else:
                            st.error(f'**{symbol}** | {result.signal.upper()} | {result.timeframe}')
                        st.markdown(f'**Score:** `{result.score:.1f}`')
                        st.markdown(f'**Price:** `{result.price:.4f}`')
                        st.markdown(f'**Timeframe:** `{result.timeframe}`')
                        st.markdown(f'**Displayed at:** `{result.display_time}`')
                        st.markdown(f'**Details:** {result.details}')
                        st.dataframe(
                            result.df[['open_time', 'open', 'high', 'low', 'close', 'volume']].tail(10)
                        )
                other_results = [r for r in results if r.signal not in {'buy', 'sell'}]
                if other_results:
                    with st.expander('Other timeframes (no active signal)', expanded=False):
                        for result in other_results:
                            st.write(
                                f'{result.timeframe}: {result.signal.upper()} — {result.details}'
                            )
    else:
        st.info('No active signals found for selected symbols and timeframes.')

    if neutral_symbols:
        with st.expander('Symbols without active signals', expanded=False):
            for symbol, results in neutral_symbols:
                st.write(f'**{symbol}**')
                for result in results:
                    st.write(f'- {result.timeframe}: {result.signal.upper()} — {result.details}')

    if errors:
        with st.expander('Load errors', expanded=False):
            for raw_symbol, timeframe, exc in errors:
                st.error(f'{raw_symbol} @ {timeframe}: {exc}')


def main():
    config = Config.load()
    client = BinanceDataClient(config)
    strategies = {
        'Main Strategy': (MainEMAStrategy(config), config.symbols_main or config.symbols),
        'Order Block Matrix': (OrderBlockMatrixStrategy(config), config.symbols),
        'Smart Money Order Block': (SmartMoneyOrderBlockStrategy(config), config.symbols),
    }

    st.set_page_config(page_title='Binance Strategy Monitor', layout='wide')
    st.sidebar.title('Strategy Pages')
    page = st.sidebar.selectbox('Choose strategy page', list(strategies.keys()))

    strategy, symbols = strategies[page]
    render_strategy_page(strategy, symbols, client, config)


if __name__ == '__main__':
    main()
