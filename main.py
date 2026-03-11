import threading
import time
import schedule
from datetime import datetime
from flask import Flask
from config import CONFIG
from exchange import BinanceManager
from indicators import LegendIndicators
from signal_generator import SignalGenerator
from news_filter import NewsFilter
from telegram_bot import TelegramManager
from chart_generator import ChartGenerator

app = Flask(__name__)


class LegendTradingBot:
    """Main Legend Trading Bot"""

    def __init__(self):
        print("🚀 Initializing Legend Trading Bot...")
        self.exchange    = BinanceManager()
        self.signal_gen  = SignalGenerator()
        self.news_filter = NewsFilter()
        self.telegram    = TelegramManager()
        self.chart_gen   = ChartGenerator()
        self.pairs       = CONFIG['PAIRS']
        self.timeframes  = CONFIG['TIMEFRAMES']
        self.signals_today = 0
        self.last_status   = None
        print(f"✅ Bot ready! Monitoring {len(self.pairs)} pairs")

    def scan_pair(self, symbol):
        """Scan satu pair — return (signal, df_4h, df_1h, df_15m) atau None"""
        try:
            df_4h  = self.exchange.fetch_ohlcv(symbol, self.timeframes['trend'],     200)
            df_1h  = self.exchange.fetch_ohlcv(symbol, self.timeframes['tactics'],   200)
            df_15m = self.exchange.fetch_ohlcv(symbol, self.timeframes['execution'], 200)

            if df_4h is None or df_1h is None or df_15m is None:
                return None, None, None, None

            funding = self.exchange.get_funding_rate(symbol)
            balance = self.exchange.get_balance()

            # Add indicators (save for chart)
            df_4h_ind  = LegendIndicators.add_all_indicators(df_4h.copy())
            df_1h_ind  = LegendIndicators.add_all_indicators(df_1h.copy())
            df_15m_ind = LegendIndicators.add_all_indicators(df_15m.copy())

            signal = self.signal_gen.generate_signal(
                symbol, df_4h, df_1h, df_15m, balance, funding
            )
            return signal, df_4h_ind, df_1h_ind, df_15m_ind

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            return None, None, None, None

    def scan_all_pairs(self):
        """Scan semua pair"""
        print(f"\n{'='*50}")
        print(f"🔍 Scanning {len(self.pairs)} pairs — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")

        # Check market status
        market_data = {}
        for symbol in self.pairs:
            df = self.exchange.fetch_ohlcv(symbol, '1h', 50)
            if df is not None:
                try:
                    df = LegendIndicators.add_all_indicators(df)
                    market_data[symbol] = df
                except:
                    pass

        status = self.news_filter.get_combined_status(market_data)
        self.last_status = status
        self.telegram.send_status(status, self.signals_today)

        if not status['can_trade']:
            print("⛔ Trading paused due to market conditions")
            return

        signals_found = 0
        for symbol in self.pairs:
            print(f"Scanning {symbol}...")
            signal, df_4h, df_1h, df_15m = self.scan_pair(symbol)

            if signal:
                if status['reduce_size']:
                    signal['position']['position_size'] *= 0.5
                    signal['position']['margin'] *= 0.5

                # Kirim signal text
                self.telegram.send_signal(signal)
                time.sleep(1)

                # Kirim 1H chart
                try:
                    chart_1h = self.chart_gen.create_chart(df_1h, signal, '1H')
                    caption = f"📊 {signal['symbol']} {signal['direction']} | Score: {signal['score']}/100"
                    self.telegram.send_photo(chart_1h, caption)
                    time.sleep(1)
                except Exception as e:
                    print(f"Chart 1H error: {e}")

                # Kirim multi-timeframe chart
                try:
                    chart_mt = self.chart_gen.create_multi_timeframe(df_4h, df_1h, df_15m, signal)
                    self.telegram.send_photo(chart_mt, "🎯 Multi-Timeframe Analysis (4H / 1H / 15m)")
                except Exception as e:
                    print(f"Chart MTF error: {e}")

                self.signals_today += 1
                signals_found += 1
                print(f"✅ Signal: {symbol} {signal['direction']} | Score: {signal['score']}")
                time.sleep(2)
            else:
                print(f"❌ No signal: {symbol}")

            time.sleep(3)

        print(f"\n📊 Scan complete. Signals: {signals_found}")

    def reset_daily_stats(self):
        self.signals_today = 0
        print("📅 Daily stats reset")

    def run(self):
        self.telegram.send_startup(len(self.pairs))
        self.scan_all_pairs()

        schedule.every(15).minutes.do(self.scan_all_pairs)
        schedule.every().day.at("00:00").do(self.reset_daily_stats)

        while True:
            schedule.run_pending()
            time.sleep(1)


@app.route("/")
def home():
    return "Legend Trading Bot Running! 🔥", 200


def start_bot():
    bot = LegendTradingBot()
    bot.run()


if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=8080)
