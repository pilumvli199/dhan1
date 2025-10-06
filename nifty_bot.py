import asyncio
import os
from telegram import Bot
from dhanhq import dhanhq
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========================
# CONFIGURATION
# ========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

# Nifty 50 Index Security ID
NIFTY_50_SECURITY_ID = "13"

# ========================
# BOT CODE
# ========================

class NiftyLTPBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        self.running = True
        logger.info("Bot initialized successfully")
    
    def get_nifty_ltp(self):
        """Dhan v2 API वरून Nifty 50 चा LTP घेतो"""
        try:
            # Dhan v2 Market Quote API
            # Request structure: {"IDX_I": [security_ids]}
            instruments = {
                "IDX_I": [int(NIFTY_50_SECURITY_ID)]
            }
            
            # Get OHLC + LTP data
            response = self.dhan.get_market_quote(instruments)
            
            logger.info(f"API Response: {response}")
            
            if response and 'data' in response and 'IDX_I' in response['data']:
                nifty_data = response['data']['IDX_I'].get(NIFTY_50_SECURITY_ID, {})
                
                if nifty_data and 'last_price' in nifty_data:
                    ltp = nifty_data['last_price']
                    ohlc = nifty_data.get('ohlc', {})
                    
                    data = {
                        'ltp': ltp,
                        'open': ohlc.get('open', 0),
                        'high': ohlc.get('high', 0),
                        'low': ohlc.get('low', 0),
                        'close': ohlc.get('close', 0)
                    }
                    
                    # Calculate change
                    if data['close'] > 0:
                        data['change'] = ltp - data['close']
                        data['change_pct'] = (data['change'] / data['close']) * 100
                    else:
                        data['change'] = 0
                        data['change_pct'] = 0
                    
                    logger.info(f"LTP fetched: {ltp}")
                    return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting LTP: {e}")
            return None
    
    async def send_ltp_message(self, data):
        """Telegram वर LTP पाठवतो"""
        try:
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            # Change indicator
            change_emoji = "🟢" if data['change'] >= 0 else "🔴"
            change_sign = "+" if data['change'] >= 0 else ""
            
            message = f"📊 *NIFTY 50 LIVE*\n\n"
            message += f"💰 LTP: ₹{data['ltp']:,.2f}\n"
            
            if data['change'] != 0:
                message += f"{change_emoji} Change: {change_sign}{data['change']:,.2f} ({change_sign}{data['change_pct']:.2f}%)\n\n"
            
            if data['open'] > 0:
                message += f"🔵 Open: ₹{data['open']:,.2f}\n"
            if data['high'] > 0:
                message += f"📈 High: ₹{data['high']:,.2f}\n"
            if data['low'] > 0:
                message += f"📉 Low: ₹{data['low']:,.2f}\n"
            if data['close'] > 0:
                message += f"⚪ Prev Close: ₹{data['close']:,.2f}\n"
            
            message += f"\n🕐 Time: {timestamp}\n"
            message += f"_Updated every minute_ ⏱️"
            
            await self.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Message sent - LTP: {data['ltp']}")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def run(self):
        """Main loop - दर मिनिटाला LTP पाठवतो"""
        logger.info("🚀 Bot started! Sending Nifty 50 LTP every minute...")
        
        await self.send_startup_message()
        
        while self.running:
            try:
                data = self.get_nifty_ltp()
                
                if data:
                    await self.send_ltp_message(data)
                else:
                    logger.warning("Could not fetch LTP - Market might be closed or API issue")
                
                # 1 minute wait
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def send_startup_message(self):
        """Bot सुरू झाल्यावर message पाठवतो"""
        try:
            msg = "🤖 *Nifty 50 LTP Bot Started!*\n\n"
            msg += "तुम्हाला आता दर मिनिटाला Nifty 50 चा Live LTP मिळेल! 📈\n\n"
            msg += "✅ Powered by Dhan API v2\n"
            msg += "🚂 Deployed on Railway.app\n\n"
            msg += "_Market Hours: 9:15 AM - 3:30 PM (Mon-Fri)_"
            
            await self.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode='Markdown'
            )
            logger.info("Startup message sent")
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")


# ========================
# BOT RUN करा
# ========================
if __name__ == "__main__":
    try:
        # Environment variables check
        if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN]):
            logger.error("❌ Missing environment variables!")
            logger.error("Please set: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN")
            exit(1)
        
        bot = NiftyLTPBot()
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
