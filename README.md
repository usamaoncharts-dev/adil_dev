# Binance Strategy Bot

This repository contains a Python bot designed to monitor three separate Binance strategies and send email alerts when a strategy triggers a buy or sell signal.

## Architecture

- `bot/config.py` - Loads `.env` settings and symbol lists.
- `bot/exchange.py` - Fetches Binance market data using the Binance API.
- `bot/notifier.py` - Sends email alerts through SMTP.
- `bot/strategies/` - Contains one module per strategy.
  - `main_strategy.py`
  - `order_block_matrix_strategy.py`
  - `smart_money_orderblock_strategy.py`
- `bot/run_bot.py` - Main polling loop, separate signal generation per strategy.
- `bot/streamlit_app.py` - Streamlit frontend for monitoring each strategy on its own page.

## Setup

1. Create a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Ensure `.env` contains valid Binance API credentials and SMTP settings.

## Usage

Run the bot from the workspace root:

```powershell
python -m bot.run_bot
```

Run the Streamlit dashboard from the workspace root or inside the `bot` folder:

```powershell
streamlit run bot/streamlit_app.py
```

If you are already inside `bot/`, the app still resolves the package root automatically.

## Notes

- Each strategy is kept separate and uses its own evaluation logic.
- `SYMBOLS_main` is used for the main strategy as requested.
- `SYMBOLS` is used for the two indicator-based strategies.
- The Streamlit app places each strategy on its own page via the sidebar.
