import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io


class ChartGenerator:
    """Generate professional trading charts"""

    def __init__(self):
        plt.style.use('dark_background')
        self.colors = {
            'bg':     '#0d1117',
            'grid':   '#21262d',
            'up':     '#00d084',
            'down':   '#ff4757',
            'text':   '#c9d1d9',
            'ema9':   '#ff6b6b',
            'ema21':  '#4ecdc4',
            'ema55':  '#45b7d1',
            'ema200': '#96ceb4',
            'buy':    '#00d084',
            'sell':   '#ff4757'
        }

    def prepare_data(self, df):
        """Prepare dataframe for charting"""
        df = df.copy().tail(80)
        df.index = pd.to_datetime(df['timestamp'])
        df = df.rename(columns={
            'open': 'Open', 'high': 'High',
            'low': 'Low', 'close': 'Close', 'volume': 'Volume'
        })
        return df

    def _plot_candles(self, ax, df):
        """Plot candlesticks"""
        for i, (idx, row) in enumerate(df.iterrows()):
            color = self.colors['up'] if row['Close'] >= row['Open'] else self.colors['down']
            height = abs(row['Close'] - row['Open'])
            bottom = min(row['Close'], row['Open'])
            ax.bar(i, height, 0.6, bottom=bottom, color=color, alpha=0.8)
            ax.plot([i, i], [row['Low'], row['High']], color=color, linewidth=0.8)

        # Set x ticks
        step = max(1, len(df) // 8)
        ticks = range(0, len(df), step)
        labels = [df.index[i].strftime('%m/%d %H:%M') for i in ticks]
        ax.set_xticks(list(ticks))
        ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=7, color=self.colors['text'])

    def _plot_signal_levels(self, ax, df, signal):
        """Plot entry, stop loss, take profit lines"""
        n = len(df)
        entry = signal['entry']
        stop  = signal['stop_loss']
        tp    = signal['take_profit']

        ax.axhline(y=entry, color=self.colors['buy'],  linestyle='-',  linewidth=2, alpha=0.9,
                   label=f"Entry: ${entry:,.4f}")
        ax.axhline(y=stop,  color=self.colors['sell'], linestyle='--', linewidth=2, alpha=0.9,
                   label=f"SL: ${stop:,.4f}")
        ax.axhline(y=tp,    color=self.colors['buy'],  linestyle='--', linewidth=2, alpha=0.9,
                   label=f"TP: ${tp:,.4f}")

        x_range = range(n)
        ax.fill_between(x_range, stop,  entry, alpha=0.08, color='red')
        ax.fill_between(x_range, entry, tp,    alpha=0.08, color='green')

    def _add_info_box(self, fig, signal):
        """Add signal info box"""
        pos = signal['position']
        info = (
            f"Signal: {signal['direction']} | Score: {signal['score']}/100\n"
            f"Entry: ${signal['entry']:,.4f} | Lev: {pos['leverage']}x\n"
            f"SL: ${signal['stop_loss']:,.4f} ({pos['stop_distance_percent']:.2f}%)\n"
            f"TP: ${signal['take_profit']:,.4f} | R:R 1:{signal['risk_reward']:.1f}\n"
            f"RSI: {signal['indicators']['rsi']} | ADX: {signal['indicators']['adx']}\n"
            f"ATR: {signal['indicators']['atr_percent']}%"
        )
        fig.text(0.01, 0.01, info, fontsize=8, color=self.colors['text'],
                 family='monospace', verticalalignment='bottom',
                 bbox=dict(boxstyle='round', facecolor=self.colors['bg'],
                           edgecolor=self.colors['grid'], alpha=0.9))

    def create_chart(self, df, signal=None, timeframe='1H'):
        """Create single-timeframe chart with indicators"""
        df = self.prepare_data(df)

        fig = plt.figure(figsize=(12, 10), facecolor=self.colors['bg'])
        gs  = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.05)

        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax3 = fig.add_subplot(gs[2])

        for ax in [ax1, ax2, ax3]:
            ax.set_facecolor(self.colors['bg'])

        # Candles
        self._plot_candles(ax1, df)

        x = range(len(df))

        # EMAs
        if 'EMA_9'   in df.columns: ax1.plot(x, df['EMA_9'].values,   color=self.colors['ema9'],   linewidth=1.5, label='EMA9')
        if 'EMA_21'  in df.columns: ax1.plot(x, df['EMA_21'].values,  color=self.colors['ema21'],  linewidth=1.5, label='EMA21')
        if 'EMA_55'  in df.columns: ax1.plot(x, df['EMA_55'].values,  color=self.colors['ema55'],  linewidth=1.5, label='EMA55')
        if 'EMA_200' in df.columns: ax1.plot(x, df['EMA_200'].values, color=self.colors['ema200'], linewidth=2.0, label='EMA200')

        # Bollinger Bands
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            ax1.fill_between(x, df['bb_upper'].values, df['bb_lower'].values, alpha=0.08, color='gray')
            ax1.plot(x, df['bb_upper'].values, '--', color='gray', alpha=0.4, linewidth=0.8)
            ax1.plot(x, df['bb_lower'].values, '--', color='gray', alpha=0.4, linewidth=0.8)

        # Signal levels
        if signal:
            self._plot_signal_levels(ax1, df, signal)

        # Volume
        vol_colors = [self.colors['up'] if df['Close'].iloc[i] >= df['Open'].iloc[i]
                      else self.colors['down'] for i in range(len(df))]
        ax2.bar(x, df['Volume'].values, color=vol_colors, alpha=0.7)
        ax2.set_ylabel('Volume', color=self.colors['text'], fontsize=9)

        # RSI
        if 'rsi' in df.columns:
            ax3.plot(x, df['rsi'].values, color='#ffd93d', linewidth=1.5, label='RSI')
            ax3.axhline(y=70, color='red',   linestyle='--', alpha=0.5)
            ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5)
            ax3.fill_between(x, 30, 70, alpha=0.05, color='gray')
            ax3.set_ylim(0, 100)
            ax3.set_ylabel('RSI', color=self.colors['text'], fontsize=9)

        # Styling
        symbol = signal['symbol'] if signal else 'Chart'
        ax1.set_title(f"{symbol} — {timeframe} | Legend Trading Bot",
                      color=self.colors['text'], fontsize=13, fontweight='bold', pad=10)
        ax1.legend(loc='upper left', facecolor=self.colors['bg'],
                   edgecolor=self.colors['grid'], labelcolor=self.colors['text'], fontsize=8)

        for ax in [ax1, ax2, ax3]:
            ax.tick_params(colors=self.colors['text'])
            ax.grid(True, alpha=0.2, color=self.colors['grid'])

        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)

        if signal:
            self._add_info_box(fig, signal)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=130, facecolor=self.colors['bg'],
                    edgecolor='none', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf

    def create_multi_timeframe(self, df_4h, df_1h, df_15m, signal):
        """Create multi-timeframe chart (4H / 1H / 15m)"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 12), facecolor=self.colors['bg'])
        fig.patch.set_facecolor(self.colors['bg'])

        timeframes = [
            (df_4h,  '4H  (Trend)',     axes[0], False),
            (df_1h,  '1H  (Tactics)',   axes[1], True),
            (df_15m, '15m (Execution)', axes[2], False),
        ]

        for df, label, ax, show_signal in timeframes:
            df_prep = self.prepare_data(df)
            ax.set_facecolor(self.colors['bg'])
            self._plot_candles(ax, df_prep)

            x = range(len(df_prep))
            if 'EMA_9'  in df_prep.columns: ax.plot(x, df_prep['EMA_9'].values,  color=self.colors['ema9'],  linewidth=1, label='EMA9')
            if 'EMA_21' in df_prep.columns: ax.plot(x, df_prep['EMA_21'].values, color=self.colors['ema21'], linewidth=1, label='EMA21')
            if 'EMA_55' in df_prep.columns: ax.plot(x, df_prep['EMA_55'].values, color=self.colors['ema55'], linewidth=1, label='EMA55')

            if show_signal and signal:
                self._plot_signal_levels(ax, df_prep, signal)

            ax.set_title(f"{signal['symbol']} — {label}", color=self.colors['text'],
                         fontsize=11, fontweight='bold')
            ax.legend(loc='upper left', fontsize=7, facecolor=self.colors['bg'],
                      edgecolor=self.colors['grid'], labelcolor=self.colors['text'])
            ax.tick_params(colors=self.colors['text'])
            ax.grid(True, alpha=0.2, color=self.colors['grid'])

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=110, facecolor=self.colors['bg'],
                    edgecolor='none', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
