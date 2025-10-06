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
# CONFIGURATION - Environment Variables वरून घ्या
# ========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

# Nifty 50 Security ID
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
        """Dhan वरून Nifty 50 चा LTP घेतो"""
        try:
            ltp_data = self.dhan.get_ltp_data(
                exchange_segment=self.dhan.IDX,
                security_id=NIFTY_50_SECURITY_ID
            )
            
            if ltp_data and 'data' in ltp_data:
                ltp = ltp_data['data']['LTP']
                logger.info(f"LTP fetched: {ltp}")
                return ltp
            return None
            
        except Exception as e:
            logger.error(f"Error getting LTP: {e}")
            return None
    
    async def send_ltp_message(self, ltp):
        """Telegram वर LTP पाठवतो"""
        try:
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message = f"📊 *NIFTY 50 LTP*\n\n"
            message += f"💰 Price: ₹{ltp}\n"
            message += f"🕐 Time: {timestamp}\n"
            message += f"\n_Updated every minute_ ⏱️"
            
            await self.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Message sent - LTP: {ltp}")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def run(self):
        """Main loop - दर मिनिटाला LTP पाठवतो"""
        logger.info("🚀 Bot started! Sending Nifty 50 LTP every minute...")
        
        await self.send_startup_message()
        
        while self.running:
            try:
                ltp = self.get_nifty_ltp()
                
                if ltp:
                    await self.send_ltp_message(ltp)
                else:
                    logger.warning("Could not fetch LTP")
                
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
            msg += "तुम्हाला आता दर मिनिटाला Nifty 50 चा LTP मिळेल! 📈\n"
            msg += f"Deployed on Railway.app 🚂"
            
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
