import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # Telegram
    'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN', '8546209847:AAHexPmRRvKGsnaZQQSgVFK_DFEPoe_8wXE'),
    'TELEGRAM_CHAT_ID': int(os.getenv('TELEGRAM_CHAT_ID', '1603606771')),

    # Trading
    'RISK_PER_TRADE': float(os.getenv('RISK_PER_TRADE', 2)),
    'MAX_LEVERAGE': int(os.getenv('MAX_LEVERAGE', 10)),
    'MAX_DAILY_LOSS': float(os.getenv('MAX_DAILY_LOSS', 6)),
    'MIN_CONFLUENCE_SCORE': int(os.getenv('MIN_CONFLUENCE_SCORE', 70)),

    # Account (signal-only mode, no API key needed)
    'DEFAULT_BALANCE': float(os.getenv('DEFAULT_BALANCE', 10000)),

    # Pairs
    'PAIRS': [
        'BTCUSDT', 'ETHUSDT', 'SOLUSDT',
        'BNBUSDT', 'XRPUSDT', 'DOGEUSDT',
        'LINKUSDT', 'ADAUSDT', 'HYPEUSDT'
    ],

    # Timeframes
    'TIMEFRAMES': {
        'trend': '4h',
        'tactics': '1h',
        'execution': '15m'
    },

    # Risk
    'MAX_POSITIONS': 3,
}
