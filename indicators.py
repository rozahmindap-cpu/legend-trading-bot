import pandas as pd
import numpy as np
import ta

class LegendIndicators:
    """Semua indikator yang dipakai Legend Trading Bot"""

    @staticmethod
    def supertrend(df, period=10, multiplier=3):
        """Manual Supertrend implementation"""
        hl2 = (df['high'] + df['low']) / 2
        atr = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=period)

        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        direction = pd.Series(1, index=df.index)
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i - 1]:
                direction.iloc[i] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i - 1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i - 1]
        return direction

    @staticmethod
    def add_all_indicators(df):
        """Tambah semua indikator ke dataframe"""
        df = df.copy()

        # === TREND ===
        for period in [9, 21, 55, 89, 200]:
            df[f'EMA_{period}'] = ta.trend.ema_indicator(df['close'], window=period)

        # Ichimoku
        ichimoku = ta.trend.IchimokuIndicator(
            high=df['high'], low=df['low'],
            window1=9, window2=26, window3=52
        )
        df['tenkan_sen'] = ichimoku.ichimoku_conversion_line()
        df['kijun_sen'] = ichimoku.ichimoku_base_line()
        df['senkou_span_a'] = ichimoku.ichimoku_a()
        df['senkou_span_b'] = ichimoku.ichimoku_b()

        # ADX
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        df['adx'] = adx.adx()
        df['di_plus'] = adx.adx_pos()
        df['di_minus'] = adx.adx_neg()

        # Supertrend
        df['supertrend'] = LegendIndicators.supertrend(df, period=10, multiplier=3)

        # PSAR
        psar_ind = ta.trend.PSARIndicator(df['high'], df['low'], df['close'])
        df['psar'] = psar_ind.psar()

        # === MOMENTUM ===
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)

        stoch_rsi = ta.momentum.StochRSIIndicator(df['close'])
        df['stoch_rsi_k'] = stoch_rsi.stochrsi_k()
        df['stoch_rsi_d'] = stoch_rsi.stochrsi_d()

        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()

        df['cci'] = ta.trend.cci(df['high'], df['low'], df['close'])
        df['williams_r'] = ta.momentum.williams_r(df['high'], df['low'], df['close'])
        df['awesome_osc'] = ta.momentum.awesome_oscillator(df['high'], df['low'])

        # === VOLATILITY ===
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
        df['atr_percent'] = (df['atr'] / df['close']) * 100

        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_width'] = bb.bollinger_wband()

        # === VOLUME ===
        df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
        df['vwap'] = ta.volume.volume_weighted_average_price(
            df['high'], df['low'], df['close'], df['volume']
        )

        return df

    @staticmethod
    def calculate_confluence_score(df):
        """Hitung confluence score 0-100"""
        score = 0
        details = {}

        latest = df.iloc[-1]

        # === TREND SCORE (max 25) ===
        trend_score = 0

        ema_bull = (latest['EMA_9'] > latest['EMA_21'] > latest['EMA_55'] >
                    latest['EMA_89'] > latest['EMA_200'])
        ema_bear = (latest['EMA_9'] < latest['EMA_21'] < latest['EMA_55'] <
                    latest['EMA_89'] < latest['EMA_200'])

        if ema_bull:
            trend_score += 8
            details['ema'] = 'BULLISH_STACK'
        elif ema_bear:
            trend_score += 8
            details['ema'] = 'BEARISH_STACK'
        else:
            details['ema'] = 'MIXED'

        price_above_cloud = latest['close'] > max(latest['senkou_span_a'], latest['senkou_span_b'])
        tk_cross_bull = latest['tenkan_sen'] > latest['kijun_sen']
        if price_above_cloud and tk_cross_bull:
            trend_score += 7
            details['ichimoku'] = 'STRONG_BULLISH'
        elif not price_above_cloud and not tk_cross_bull:
            trend_score += 7
            details['ichimoku'] = 'STRONG_BEARISH'
        else:
            details['ichimoku'] = 'MIXED'

        if latest['adx'] > 25:
            trend_score += 5
            details['adx'] = f"STRONG_{latest['adx']:.1f}"
        else:
            details['adx'] = f"WEAK_{latest['adx']:.1f}"

        if latest['supertrend'] == 1:
            trend_score += 5
            details['supertrend'] = 'BULLISH'
        else:
            trend_score += 5
            details['supertrend'] = 'BEARISH'

        score += trend_score
        details['trend_score'] = trend_score

        # === MOMENTUM SCORE (max 25) ===
        mom_score = 0

        rsi_bull = 40 < latest['rsi'] < 70
        rsi_bear = 30 < latest['rsi'] < 60

        if rsi_bull and ema_bull:
            mom_score += 8
            details['rsi'] = f"BULLISH_{latest['rsi']:.1f}"
        elif rsi_bear and ema_bear:
            mom_score += 8
            details['rsi'] = f"BEARISH_{latest['rsi']:.1f}"
        else:
            details['rsi'] = f"NEUTRAL_{latest['rsi']:.1f}"

        stoch_bull = latest['stoch_rsi_k'] > latest['stoch_rsi_d'] and latest['stoch_rsi_k'] < 0.8
        stoch_bear = latest['stoch_rsi_k'] < latest['stoch_rsi_d'] and latest['stoch_rsi_k'] > 0.2

        if stoch_bull and ema_bull:
            mom_score += 7
            details['stoch'] = 'BULLISH_CROSS'
        elif stoch_bear and ema_bear:
            mom_score += 7
            details['stoch'] = 'BEARISH_CROSS'
        else:
            details['stoch'] = 'NEUTRAL'

        macd_bull = latest['macd'] > latest['macd_signal'] and latest['macd_hist'] > 0
        macd_bear = latest['macd'] < latest['macd_signal'] and latest['macd_hist'] < 0

        if macd_bull and ema_bull:
            mom_score += 5
            details['macd'] = 'BULLISH'
        elif macd_bear and ema_bear:
            mom_score += 5
            details['macd'] = 'BEARISH'
        else:
            details['macd'] = 'MIXED'

        if abs(latest['cci']) < 100 and abs(latest['williams_r'] + 50) < 30:
            mom_score += 5
            details['secondary'] = 'ALIGNED'
        else:
            details['secondary'] = 'DIVERGENT'

        score += mom_score
        details['momentum_score'] = mom_score

        # === VOLUME & STRUCTURE (max 25) ===
        vol_score = 0

        obv_rising = latest['obv'] > df['obv'].iloc[-10]
        if obv_rising and ema_bull:
            vol_score += 6
            details['obv'] = 'CONFIRMING_RISING'
        elif not obv_rising and ema_bear:
            vol_score += 6
            details['obv'] = 'CONFIRMING_FALLING'
        else:
            details['obv'] = 'DIVERGENT'

        above_vwap = latest['close'] > latest['vwap']
        if above_vwap and ema_bull:
            vol_score += 5
            details['vwap'] = 'ABOVE'
        elif not above_vwap and ema_bear:
            vol_score += 5
            details['vwap'] = 'BELOW'
        else:
            details['vwap'] = 'MIXED'

        avg_vol = df['volume'].tail(20).mean()
        if latest['volume'] > avg_vol * 1.5:
            vol_score += 5
            details['volume'] = f"SPIKE_{latest['volume']/avg_vol:.1f}x"
        else:
            details['volume'] = 'NORMAL'

        if latest['atr_percent'] < 5:
            vol_score += 4
            details['atr'] = f"NORMAL_{latest['atr_percent']:.2f}%"
        elif latest['atr_percent'] < 8:
            vol_score += 2
            details['atr'] = f"ELEVATED_{latest['atr_percent']:.2f}%"
        else:
            details['atr'] = f"EXTREME_{latest['atr_percent']:.2f}%"

        score += vol_score
        details['volume_score'] = vol_score

        # === CONTEXT (max 25) ===
        context_score = 25

        ema9_dist = abs(latest['close'] - latest['EMA_9']) / latest['close'] * 100
        if ema9_dist > 3:
            context_score -= 5
            details['chase_warning'] = f"FAR_FROM_EMA_{ema9_dist:.2f}%"
        else:
            details['chase_warning'] = 'NONE'

        recent_atr = df['atr_percent'].tail(5).mean()
        if recent_atr > latest['atr_percent'] * 1.5:
            context_score -= 5
            details['vol_spike'] = 'RECENT_SPIKE'
        else:
            details['vol_spike'] = 'STABLE'

        score += max(0, context_score)
        details['context_score'] = max(0, context_score)

        # Direction
        if ema_bull and trend_score >= 20 and mom_score >= 15:
            direction = 'LONG'
        elif ema_bear and trend_score >= 20 and mom_score >= 15:
            direction = 'SHORT'
        else:
            direction = 'NEUTRAL'

        details['direction'] = direction
        details['total_score'] = score

        return score, direction, details
