"""
Notification System
Handles Telegram, Email, and SMS notifications
"""

import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import os
from datetime import datetime

class NotificationSystem:
    def __init__(self):
        self.telegram_enabled = False
        self.email_enabled = False
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.email_smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.email_smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_to = os.getenv('EMAIL_TO')
        
        self._setup_notifications()
    
    def _setup_notifications(self):
        """Setup notification channels based on environment variables"""
        if self.telegram_bot_token and self.telegram_chat_id:
            self.telegram_enabled = True
            print("📱 Telegram notifications enabled")
        
        if self.email_username and self.email_password and self.email_to:
            self.email_enabled = True
            print("📧 Email notifications enabled")
    
    async def send_trade_opened(self, trade: Dict):
        """Send notification when trade is opened"""
        message = f"🚀 Trade Opened\n"
        message += f"Instrument: {trade['instrument']}\n"
        message += f"Direction: {trade['direction']}\n"
        message += f"Setup: {trade['setup_type']}\n"
        message += f"Entry: {trade['entry_price']}\n"
        message += f"SL: {trade['stop_loss']}\n"
        message += f"TP: {trade['take_profit']}\n"
        message += f"Risk: ${trade['risk_amount']:.2f}"
        
        await self._send_notification("Trade Opened", message)
    
    async def send_trade_closed(self, trade: Dict, pnl: float, exit_reason: str):
        """Send notification when trade is closed"""
        emoji = "💰" if pnl > 0 else "📉"
        message = f"{emoji} Trade Closed\n"
        message += f"Instrument: {trade['instrument']}\n"
        message += f"Direction: {trade['direction']}\n"
        message += f"P&L: ${pnl:.2f}\n"
        message += f"Exit Reason: {exit_reason}\n"
        message += f"Duration: {self._calculate_duration(trade['entry_time'])}"
        
        await self._send_notification("Trade Closed", message)
    
    async def send_daily_limit_reached(self):
        """Send notification when daily trade limit is reached"""
        message = "⏸️ Daily trade limit reached (3/3)\nBot will resume trading tomorrow."
        await self._send_notification("Daily Limit Reached", message)
    
    async def send_max_drawdown_reached(self, current_drawdown: float, max_allowed: float):
        """Send notification when maximum drawdown is reached"""
        message = f"🛑 Maximum Drawdown Reached\n"
        message += f"Current: {current_drawdown:.2f}%\n"
        message += f"Max Allowed: {max_allowed:.2f}%\n"
        message += f"Trading paused for today."
        
        await self._send_notification("Max Drawdown Alert", message)
    
    async def send_bot_status(self, status: str):
        """Send bot start/stop notifications"""
        emoji = "🟢" if status == "started" else "🔴"
        message = f"{emoji} Bot {status.upper()}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await self._send_notification(f"Bot {status.title()}", message)
    
    async def send_error_alert(self, error_type: str, error_message: str):
        """Send error notifications"""
        message = f"❌ Error Alert\n"
        message += f"Type: {error_type}\n"
        message += f"Message: {error_message}\n"
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await self._send_notification("Error Alert", message)
    
    async def _send_notification(self, subject: str, message: str):
        """Send notification via all enabled channels"""
        if self.telegram_enabled:
            await self._send_telegram(message)
        
        if self.email_enabled:
            await self._send_email(subject, message)
    
    async def _send_telegram(self, message: str):
        """Send Telegram notification"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        print("📱 Telegram notification sent")
                    else:
                        print(f"❌ Telegram notification failed: {response.status}")
        
        except Exception as e:
            print(f"❌ Telegram error: {str(e)}")
    
    async def _send_email(self, subject: str, message: str):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = self.email_to
            msg['Subject'] = f"SST Bot - {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.email_smtp_server, self.email_smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, self.email_to, text)
            server.quit()
            
            print("📧 Email notification sent")
        
        except Exception as e:
            print(f"❌ Email error: {str(e)}")
    
    def _calculate_duration(self, entry_time: str) -> str:
        """Calculate trade duration"""
        try:
            entry = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
            now = datetime.now()
            duration = now - entry
            
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"