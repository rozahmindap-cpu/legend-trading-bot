import requests
from config import CONFIG

class TelegramManager:
    """Manage Telegram notifications"""

    def __init__(self):
        self.token = CONFIG['TELEGRAM_TOKEN']
        self.chat_id = CONFIG['TELEGRAM_CHAT_ID']
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, message):
        """Kirim pesan ke Telegram"""
        try:
            requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
        except Exception as e:
            print(f"Telegram error: {e}")

    def format_signal(self, signal):
        """Format signal jadi pesan Telegram"""
        emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
        stars = "⭐️" * (signal['score'] // 20)
        pos = signal['position']
        confidence = 'VERY HIGH' if signal['score'] >= 85 else 'HIGH'

        msg = (
            f"{emoji} <b>LEGEND SIGNAL — {signal['symbol']}</b> {emoji}\n\n"
            f"<b>⭐️ CONFLUENCE SCORE: {signal['score']}/100 {stars}</b>\n\n"
            f"📊 <b>SETUP</b>\n"
            f"Direction: <b>{signal['direction']}</b>\n"
            f"Confidence: <b>{confidence}</b>\n\n"
            f"💰 <b>ENTRY & EXIT</b>\n"
            f"Entry: <code>${signal['entry']:,.4f}</code>\n"
            f"Stop Loss: <code>${signal['stop_loss']:,.4f}</code> ({pos['stop_distance_percent']:.2f}%)\n"
            f"Take Profit: <code>${signal['take_profit']:,.4f}</code>\n"
            f"Risk/Reward: <b>1:{signal['risk_reward']:.1f}</b>\n\n"
            f"⚙️ <b>POSITION SIZE</b>\n"
            f"Leverage: <b>{pos['leverage']}x</b>\n"
            f"Position: ${pos['position_size']:,.0f}\n"
            f"Margin: ${pos['margin']:,.0f}\n"
            f"Risk: ${pos['risk_amount']:,.0f} ({CONFIG['RISK_PER_TRADE']}%)\n\n"
            f"🛡 <b>SAFETY</b>\n"
            f"Liquidation: <code>${pos['liquidation_price']:,.4f}</code>\n"
            f"Distance: {pos['liquidation_distance']:.1f}% {'✅ SAFE' if pos['safe'] else '⚠️ RISKY'}\n\n"
            f"📈 <b>INDICATORS</b>\n"
            f"RSI: {signal['indicators']['rsi']} | ADX: {signal['indicators']['adx']}\n"
            f"ATR: {signal['indicators']['atr_percent']}% | Funding: {signal['indicators']['funding_rate']:.4f}%\n\n"
            f"⏱️ TF: 4H/1H/15m | Valid: 2 jam"
        )
        return msg

    def format_status(self, status, signals_found=0):
        """Format status market"""
        status_emoji = {'NORMAL': '🟢', 'REDUCE': '🟡', 'PAUSE': '🔴'}.get(status['status'], '⚪️')
        msg = (
            f"{status_emoji} <b>MARKET STATUS</b> {status_emoji}\n\n"
            f"Status: <b>{status['status']}</b>\n\n"
            f"📅 Calendar: {status['calendar']['status']}\n"
            f"🗞 News: {status['news']['status']}\n"
            f"📊 Volatility Alerts: {len(status['volatility_alerts'])}\n\n"
            f"Can Trade: {'✅ YES' if status['can_trade'] else '❌ NO'}\n"
            f"Reduce Size: {'⚠️ YES' if status['reduce_size'] else '✅ NO'}\n\n"
            f"Signals Found Today: <b>{signals_found}</b>"
        )
        return msg

    def send_signal(self, signal):
        msg = self.format_signal(signal)
        self.send_message(msg)

    def send_status(self, status, signals_found=0):
        msg = self.format_status(status, signals_found)
        self.send_message(msg)

    def send_startup(self, pairs_count):
        self.send_message(
            f"🚀 <b>Legend Trading Bot Started!</b>\n\n"
            f"📊 Monitoring: {pairs_count} pairs\n"
            f"⏱️ TF: 4H / 1H / 15m\n"
            f"🎯 Min Score: {CONFIG['MIN_CONFLUENCE_SCORE']}/100\n"
            f"💰 Risk/Trade: {CONFIG['RISK_PER_TRADE']}%\n"
            f"⚙️ Mode: Signal Only\n\n"
            f"Scan every 15 minutes. Let's go! 🔥"
        )
