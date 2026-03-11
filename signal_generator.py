import pandas as pd
from indicators import LegendIndicators
from config import CONFIG

class SignalGenerator:
    """Generate trading signals dengan risk calculation"""

    def __init__(self):
        self.indicators = LegendIndicators()

    def calculate_dynamic_leverage(self, atr_percent):
        if atr_percent < 2:
            return min(10, CONFIG['MAX_LEVERAGE'])
        elif atr_percent < 3:
            return min(7, CONFIG['MAX_LEVERAGE'])
        elif atr_percent < 4:
            return min(5, CONFIG['MAX_LEVERAGE'])
        elif atr_percent < 6:
            return min(3, CONFIG['MAX_LEVERAGE'])
        else:
            return 1

    def calculate_position(self, entry, stop, balance, atr_percent):
        risk_amount = balance * (CONFIG['RISK_PER_TRADE'] / 100)
        stop_distance = abs(entry - stop) / entry
        if stop_distance == 0:
            stop_distance = 0.01
        leverage = self.calculate_dynamic_leverage(atr_percent)
        position_size = risk_amount / stop_distance
        margin = position_size / leverage

        if entry > stop:  # Long
            liq_price = entry * (1 - (0.9 / leverage))
        else:  # Short
            liq_price = entry * (1 + (0.9 / leverage))

        liq_distance = abs(entry - liq_price) / entry * 100

        return {
            'leverage': leverage,
            'position_size': round(position_size, 2),
            'margin': round(margin, 2),
            'risk_amount': round(risk_amount, 2),
            'stop_distance_percent': round(stop_distance * 100, 2),
            'liquidation_price': round(liq_price, 4),
            'liquidation_distance': round(liq_distance, 2),
            'safe': liq_distance > (stop_distance * 100 * 3)
        }

    def find_key_levels(self, df):
        recent = df.tail(50)
        resistance = float(recent['high'].tail(20).max())
        support = float(recent['low'].tail(20).min())
        last = df.iloc[-1]
        pivot = (last['high'] + last['low'] + last['close']) / 3
        r1 = float(2 * pivot - last['low'])
        s1 = float(2 * pivot - last['high'])
        return {
            'resistance': resistance,
            'support': support,
            'pivot': float(pivot),
            'r1': r1,
            's1': s1,
            'ema_levels': {
                'EMA9': float(last['EMA_9']),
                'EMA21': float(last['EMA_21']),
                'EMA55': float(last['EMA_55'])
            }
        }

    def generate_signal(self, symbol, df_4h, df_1h, df_15m, balance, funding_rate=0):
        """Generate complete trading signal"""
        try:
            df_4h  = self.indicators.add_all_indicators(df_4h)
            df_1h  = self.indicators.add_all_indicators(df_1h)
            df_15m = self.indicators.add_all_indicators(df_15m)
        except Exception as e:
            print(f"Indicator error for {symbol}: {e}")
            return None

        score, direction, details = self.indicators.calculate_confluence_score(df_1h)

        if score < CONFIG['MIN_CONFLUENCE_SCORE'] or direction == 'NEUTRAL':
            return None

        latest = df_1h.iloc[-1]
        levels = self.find_key_levels(df_1h)
        current_price = float(latest['close'])

        if direction == 'LONG':
            entry = max(current_price * 0.998, float(latest['EMA_9']) * 0.999)
            stop_loss = min(levels['support'] * 0.998, float(latest['EMA_21']) * 0.995)
            stop_loss = min(stop_loss, current_price * 0.97)
            take_profit = max(levels['resistance'] * 0.995, levels['r1'], current_price * 1.03)
        else:
            entry = min(current_price * 1.002, float(latest['EMA_9']) * 1.001)
            stop_loss = max(levels['resistance'] * 1.002, float(latest['EMA_21']) * 1.005)
            stop_loss = max(stop_loss, current_price * 1.03)
            take_profit = min(levels['support'] * 1.005, levels['s1'], current_price * 0.97)

        position = self.calculate_position(entry, stop_loss, balance, float(latest['atr_percent']))

        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        rr_ratio = reward / risk if risk > 0 else 0

        if rr_ratio < 1.5:
            return None

        return {
            'symbol': symbol,
            'direction': direction,
            'score': score,
            'score_details': details,
            'entry': round(entry, 4),
            'stop_loss': round(stop_loss, 4),
            'take_profit': round(take_profit, 4),
            'risk_reward': round(rr_ratio, 2),
            'position': position,
            'levels': levels,
            'indicators': {
                'rsi': round(float(latest['rsi']), 1),
                'adx': round(float(latest['adx']), 1),
                'atr_percent': round(float(latest['atr_percent']), 2),
                'funding_rate': funding_rate
            }
        }
