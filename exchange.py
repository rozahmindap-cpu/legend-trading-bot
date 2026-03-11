import ccxt
import pandas as pd
from config import CONFIG

class BinanceManager:
    """Manage Binance Futures connection (signal-only, public data)"""

    def __init__(self):
        self.exchange = ccxt.binanceusdm({
            'enableRateLimit': True,
        })
        print("✅ Exchange ready (public data, signal-only mode)")

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        """Ambil candlestick data"""
        try:
            # Convert BTCUSDT -> BTC/USDT:USDT
            if ':' not in symbol:
                base = symbol.replace('USDT', '')
                symbol_fmt = f"{base}/USDT:USDT"
            else:
                symbol_fmt = symbol

            ohlcv = self.exchange.fetch_ohlcv(symbol_fmt, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df

        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def get_funding_rate(self, symbol):
        """Ambil funding rate"""
        try:
            if ':' not in symbol:
                base = symbol.replace('USDT', '')
                symbol_fmt = f"{base}/USDT:USDT"
            else:
                symbol_fmt = symbol
            funding = self.exchange.fetchFundingRate(symbol_fmt)
            return funding['fundingRate'] * 100
        except:
            return 0

    def get_balance(self):
        """Return default balance (signal-only mode)"""
        return CONFIG['DEFAULT_BALANCE']
