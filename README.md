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

> The Streamlit dashboard includes a built-in **Documentation** page in the sidebar that explains each strategy and the metrics used.

## Streamlit Cloud deployment

Streamlit Cloud uses TOML-formatted secrets, not a `.env` file. Do not upload your `.env` directly. Instead:

1. Create a `secrets.toml` file in the `.streamlit/` folder, or use the Streamlit Cloud Secrets editor.
2. Use valid TOML syntax, for example:

```toml
API_KEY = "your_binance_api_key"
API_SECRET = "your_binance_api_secret"
EMAIL_ENABLED = true
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = "your_email@gmail.com"
EMAIL_APP_PASSWORD = "your_app_password"
EMAIL_FROM = "your_email@gmail.com"
EMAIL_TO = "your_email@gmail.com"
SYMBOLS = "BTC/USDT,ETH/USDT,SOL/USDT"
SYMBOLS_main = "BNB/USDT,XRP/USDT,PYTH/USDT"
```

3. Keep real secrets out of GitHub by using `.streamlit/secrets.toml` only locally or the Streamlit Cloud Secrets UI.

## Notes

- Each strategy is kept separate and uses its own evaluation logic.
- `SYMBOLS_main` is used for the main strategy as requested.
- `SYMBOLS` is used for the two indicator-based strategies.
- The Streamlit app places each strategy on its own page via the sidebar.
