import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import mplfinance as mpf
import pandas as pd
import numpy as np
from io import BytesIO


def generate_chart(df, signal):
    """
    Generate candlestick chart dengan indikator dan level signal.
    Returns BytesIO buffer (gambar PNG).
    """
    try:
        # Prep dataframe untuk mplfinance
        chart_df = df.tail(100).copy()
        chart_df = chart_df.set_index('timestamp')
        chart_df.index = pd.DatetimeIndex(chart_df.index)
        chart_df.columns = [c.capitalize() for c in chart_df.columns]  # Open, High, Low, Close, Volume

        symbol = signal['symbol']
        direction = signal['direction']
        entry = signal['entry']
        tp = signal['take_profit']
        sl = signal['stop_loss']
        score = signal['score']

        # Additional plots (EMAs)
        ema9  = mpf.make_addplot(df['EMA_9'].tail(100).values,  color='#00bcd4', width=1, label='EMA9')
        ema21 = mpf.make_addplot(df['EMA_21'].tail(100).values, color='#ff9800', width=1, label='EMA21')
        ema55 = mpf.make_addplot(df['EMA_55'].tail(100).values, color='#9c27b0', width=1.5, label='EMA55')

        # Style
        style = mpf.make_mpf_style(
            base_mpf_style='nightclouds',
            gridstyle='--',
            gridcolor='#333333',
            gridaxis='both',
            facecolor='#1a1a2e',
            edgecolor='#444444',
            figcolor='#1a1a2e',
            marketcolors=mpf.make_marketcolors(
                up='#26a69a', down='#ef5350',
                edge='inherit', wick='inherit', volume='inherit'
            )
        )

        # Create figure
        fig, axes = mpf.plot(
            chart_df,
            type='candle',
            style=style,
            volume=True,
            addplot=[ema9, ema21, ema55],
            figsize=(12, 7),
            tight_layout=True,
            returnfig=True,
            panel_ratios=(4, 1)
        )

        ax = axes[0]

        # Draw Entry, TP, SL lines
        n = len(chart_df)
        color_entry = '#ffeb3b'
        color_tp    = '#26a69a'
        color_sl    = '#ef5350'

        ax.axhline(y=entry, color=color_entry, linestyle='--', linewidth=1.5, alpha=0.9)
        ax.axhline(y=tp,    color=color_tp,    linestyle='--', linewidth=1.5, alpha=0.9)
        ax.axhline(y=sl,    color=color_sl,    linestyle='--', linewidth=1.5, alpha=0.9)

        # Labels
        x_pos = n - 1
        ax.text(x_pos, entry, f' Entry ${entry:,.4f}', color=color_entry, fontsize=8, va='center', ha='left')
        ax.text(x_pos, tp,    f' TP ${tp:,.4f}',       color=color_tp,    fontsize=8, va='center', ha='left')
        ax.text(x_pos, sl,    f' SL ${sl:,.4f}',       color=color_sl,    fontsize=8, va='center', ha='left')

        # Title
        emoji = '🟢 LONG' if direction == 'LONG' else '🔴 SHORT'
        ax.set_title(
            f"{symbol} | {emoji} | Score: {score}/100 | RR 1:{signal['risk_reward']}",
            color='white', fontsize=11, fontweight='bold', pad=10
        )

        # Legend
        patches = [
            mpatches.Patch(color='#00bcd4', label='EMA9'),
            mpatches.Patch(color='#ff9800', label='EMA21'),
            mpatches.Patch(color='#9c27b0', label='EMA55'),
            mpatches.Patch(color=color_entry, label='Entry'),
            mpatches.Patch(color=color_tp, label='Take Profit'),
            mpatches.Patch(color=color_sl, label='Stop Loss'),
        ]
        ax.legend(handles=patches, loc='upper left', fontsize=7,
                  facecolor='#1a1a2e', edgecolor='#444', labelcolor='white')

        # Save to buffer
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#1a1a2e')
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as e:
        print(f"Chart generation error: {e}")
        return None
