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


def render_documentation_page(config: Config):
    st.title('Project Documentation')
    st.write(
        'This dashboard explains how the three strategies work, what metrics are used, '
        'and how to interpret the signals in the Streamlit app.'
    )

    st.header('Project overview')
    st.markdown(
        '''
- **Main Strategy**: 5-minute EMA crossover with momentum and sideways market filter.
- **Order Block Matrix**: Order block detection with retest and volume confirmation.
- **Smart Money Order Block**: Smart money structure using swing points, BOS/CHoCH, and breakout volume.
- **Dashboard behavior**: only active symbols with valid buy/sell signals are highlighted. Neutral symbols are collapsed.
        '''
    )

    st.header('How to use the dashboard')
    st.markdown(
        '''
1. Select a strategy page from the sidebar.
2. Active signals are shown first and expanded.
3. Each signal includes the exact candle timeframe, score, price, display time, and details.
4. Symbols without active signals are shown in a collapsed section.
5. The dashboard only shows signals for the configured symbols: `SYMBOLS_main` for Main Strategy and `SYMBOLS` for the other two strategies.
        '''
    )

    st.header('Strategy detail and metrics')
    st.subheader('Main Strategy')
    st.markdown(
        '''
- Timeframe: **5m** only.
- Uses EMA 9 / EMA 15 crossover.
- Computes a momentum angle from the EMA9 slope.
- Applies a sideways market filter using average absolute returns.
- Generates **BUY** when EMA9 crosses above EMA15, angle >= 30°, and the market is not sideways.
- Generates **SELL** when EMA15 crosses above EMA9, angle >= 30°, and the market is not sideways.
- **Score** is proportional to the EMA angle: stronger momentum produces a higher score.
        '''
    )

    st.subheader('Order Block Matrix')
    st.markdown(
        '''
- Timeframes: **15m, 1h, 4h**.
- Detects strong order block candles with large bodies and volume.
- Uses a candidate candle from 6 bars ago to define the order block zone.
- Confirms a retest and rejection in the current candle.
- Generates **BUY** when a bearish block is followed by bullish rejection and volume support.
- Generates **SELL** when a bullish block is followed by bearish rejection and volume support.
- **Score** is based on the latest candle volume relative to the 20-period average volume.
        '''
    )

    st.subheader('Smart Money Order Block')
    st.markdown(
        '''
- Timeframes: **15m, 1h, 4h**.
- Finds local swing highs and lows to build structure.
- Looks for bullish or bearish break of structure (BOS/CHoCH).
- Confirms the breakout with current candle volume compared to the 20-period average.
- Generates **BUY** for a bullish structure breakout with higher highs and volume.
- Generates **SELL** for a bearish structure breakout with lower lows and volume.
- **Score** is based on breakout volume strength.
        '''
    )

    st.header('Metric definitions')
    st.markdown(
        '''
- **Signal**: `BUY`, `SELL`, or `NEUTRAL`.
- **Score**: a strategy-specific confidence value. Higher is stronger.
- **Price**: current live price for the symbol.
- **Timeframe**: the candle resolution used to evaluate the signal.
- **Displayed at**: the exact time the dashboard rendered the symbol update.
- **Refresh interval**: same as the timeframe used for evaluation.
        '''
    )

    st.header('Score configuration')
    st.markdown(
        '''
- **Main Strategy score**: `min(100, max(0, angle * 2.0))`, where `angle` is the EMA9 slope angle calculated from the change in EMA9. This makes higher momentum produce a larger score.
- **Order Block Matrix score**: `min(100, max(0, (current_volume / average_volume) * 40))`. This means a score of 65.0 is roughly `1.625x` the average candle volume, indicating a stronger volume-based retest.
- **Smart Money Order Block score**: `min(100, (current_volume / average_volume) * 35)`. A higher breakout volume relative to the 20-period average increases the score.

> The score is an internal strength/confidence metric, not a probability. Values closer to 100 are stronger, while lower values are weaker signals.
        '''
    )

    st.header('Email documentation')
    st.markdown(
        '''
- Email alerts are sent only when a strategy produces a `BUY` or `SELL` signal.
- The email subject includes strategy, symbol, signal direction, timeframe, and score.
- The email body includes strategy name, symbol, timeframe, signal, score, price, timestamp, and signal details.
- The `Refresh interval` shown in the email is the candle timeframe that generated the signal.
- Email sending requires valid SMTP credentials in the `.env` file and `EMAIL_ENABLED=true`.
        '''
    )

    st.header('Configuration')
    st.markdown(
        '''
- `SYMBOLS_main`: symbols evaluated only by Main Strategy.
- `SYMBOLS`: symbols evaluated by Order Block Matrix and Smart Money Order Block.
- `REQUEST_TIMEOUT`: HTTP timeout in seconds.
- `REQUEST_RECV_WINDOW`: Binance recvWindow for signed requests.
- `REQUEST_MAX_RETRIES`: number of retry attempts on network timeout.
- `EMAIL_ENABLED`: enable or disable email sending.
- `EMAIL_SMTP_HOST`: SMTP server host.
- `EMAIL_SMTP_PORT`: SMTP server port.
- `EMAIL_USERNAME`: SMTP login username.
- `EMAIL_APP_PASSWORD`: SMTP login password or application-specific password.
- `EMAIL_FROM`: sender email address.
- `EMAIL_TO`: recipient email address.
        '''
    )

    st.info('The documentation page is part of the Streamlit sidebar and provides a quick reference for how each strategy evaluates signals and what the dashboard metrics mean.')


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
    pages = list(strategies.keys()) + ['Documentation']
    page = st.sidebar.selectbox('Choose strategy page', pages)

    if page == 'Documentation':
        render_documentation_page(config)
    else:
        strategy, symbols = strategies[page]
        render_strategy_page(strategy, symbols, client, config)


if __name__ == '__main__':
    main()
