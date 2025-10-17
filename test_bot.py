#!/usr/bin/env python3
"""
Simple test for DocZap bot without Supabase
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger

# Load environment variables
load_dotenv()

class SimpleDocZapBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set")

        self.application = Application.builder().token(self.token).build()
        logger.info("🤖 Simple DocZap bot initialized")

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = (
            "🏥 **Bem-vindo ao DocZap!**\n\n"
            "Este é um teste do bot. Funcionalidades:\n"
            "- /start - Esta mensagem\n"
            "- /test - Teste básico\n"
            "- Envie mensagens de voz para teste\n\n"
            "Bot está funcionando! 🎉"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"👋 User {update.effective_user.id} started bot")

    async def handle_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /test command"""
        await update.message.reply_text("✅ Bot está funcionando perfeitamente!")
        logger.info(f"🧪 Test command from user {update.effective_user.id}")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle voice messages"""
        voice = update.message.voice
        await update.message.reply_text(
            f"🎙️ Recebi sua mensagem de voz!\n"
            f"Duração: {voice.duration} segundos\n"
            f"Tamanho: {voice.file_size} bytes\n\n"
            "Em breve processarei com IA! 🤖"
        )
        logger.info(f"🎵 Voice message from user {update.effective_user.id}")

    def setup_handlers(self):
        """Setup handlers"""
        app = self.application

        app.add_handler(CommandHandler("start", self.handle_start))
        app.add_handler(CommandHandler("test", self.handle_test))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))

        logger.info("✅ Handlers registered")

    async def run(self):
        """Start the bot"""
        try:
            logger.info("🚀 Starting Simple DocZap Test Bot...")

            self.setup_handlers()

            logger.info("⚡ Bot is running! Send /start to test")
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise

def main():
    """Main entry point"""
    try:
        bot = SimpleDocZapBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()