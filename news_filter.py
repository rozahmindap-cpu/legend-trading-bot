import feedparser
from datetime import datetime

class NewsFilter:
    """Filter berita dan volatilitas"""

    def __init__(self):
        self.high_impact_events = [
            'fomc', 'fed rate', 'cpi', 'inflation', 'non-farm',
            'nfp', 'unemployment', 'gdp', 'powell', 'sec', 'etf approval',
            'binance', 'hack', 'exploit', 'shutdown', 'regulation'
        ]

    def check_economic_calendar(self):
        """Check jam berbahaya (UTC)"""
        try:
            now = datetime.utcnow()
            dangerous_hours = [13, 14, 18, 19]
            if now.hour in dangerous_hours:
                return {
                    'status': 'CAUTION',
                    'reason': f'High impact news window: {now.hour}:00 UTC',
                    'pause_trading': False,
                    'reduce_size': True
                }
            return {'status': 'CLEAR', 'pause_trading': False, 'reduce_size': False}
        except Exception as e:
            print(f"Calendar check error: {e}")
            return {'status': 'UNKNOWN', 'pause_trading': False, 'reduce_size': True}

    def check_crypto_news(self):
        """Check RSS feeds crypto news"""
        alerts = []
        try:
            # CoinDesk RSS
            coindesk = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
            for entry in coindesk.entries[:5]:
                title = entry.title.lower()
                if any(keyword in title for keyword in self.high_impact_events):
                    alerts.append({
                        'source': 'CoinDesk',
                        'title': entry.title,
                        'impact': 'HIGH' if any(x in title for x in ['sec', 'fed', 'hack', 'shutdown']) else 'MEDIUM'
                    })

            # Cointelegraph RSS
            cointelegraph = feedparser.parse('https://cointelegraph.com/rss')
            for entry in cointelegraph.entries[:5]:
                title = entry.title.lower()
                if any(keyword in title for keyword in self.high_impact_events):
                    alerts.append({
                        'source': 'Cointelegraph',
                        'title': entry.title,
                        'impact': 'HIGH' if any(x in title for x in ['sec', 'fed', 'hack', 'shutdown']) else 'MEDIUM'
                    })
        except Exception as e:
            print(f"News check error: {e}")

        high_impact = [a for a in alerts if a['impact'] == 'HIGH']

        if high_impact:
            return {
                'status': 'ALERT',
                'alerts': high_impact[:3],
                'pause_trading': True,
                'pause_duration': 60,
                'reason': f'{len(high_impact)} high impact news detected'
            }
        elif alerts:
            return {
                'status': 'CAUTION',
                'alerts': alerts[:2],
                'pause_trading': False,
                'reduce_size': True,
                'reason': 'Medium impact news detected'
            }

        return {'status': 'CLEAR', 'alerts': [], 'pause_trading': False, 'reduce_size': False}

    def check_volatility_spike(self, df, symbol):
        """Check volatility spike"""
        if df is None or len(df) < 20:
            return {'spike': False}

        current_atr = df['atr_percent'].iloc[-1]
        avg_atr = df['atr_percent'].tail(20).mean()
        price_change = abs(df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100

        if current_atr > avg_atr * 1.5:
            return {
                'spike': True,
                'type': 'ATR_SPIKE',
                'pause_trading': current_atr > 8,
                'reduce_size': True
            }
        if price_change > 3:
            return {
                'spike': True,
                'type': 'PRICE_SPIKE',
                'change': price_change,
                'pause_trading': price_change > 5,
                'reduce_size': True
            }
        return {'spike': False}

    def get_combined_status(self, market_data=None):
        """Get complete market status"""
        calendar = self.check_economic_calendar()
        news = self.check_crypto_news()

        vol_alerts = []
        if market_data:
            for symbol, df in market_data.items():
                vol_check = self.check_volatility_spike(df, symbol)
                if vol_check.get('spike'):
                    vol_alerts.append(f"{symbol}: {vol_check['type']}")

        if news.get('pause_trading') or calendar['status'] == 'DANGER':
            final_status = 'PAUSE'
        elif calendar.get('reduce_size') or news.get('reduce_size') or vol_alerts:
            final_status = 'REDUCE'
        else:
            final_status = 'NORMAL'

        return {
            'status': final_status,
            'calendar': calendar,
            'news': news,
            'volatility_alerts': vol_alerts,
            'can_trade': final_status != 'PAUSE',
            'reduce_size': final_status == 'REDUCE'
        }
