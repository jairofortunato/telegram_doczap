#!/usr/bin/env python3
"""
Simple test to verify DocZap bot can initialize properly
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot_initialization():
    """Test if bot can be initialized"""
    try:
        from main import DocZapBot

        print("🤖 Testing DocZap bot initialization...")

        # Check environment variables
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY',
            'AI_PROCESSOR_URL'
        ]

        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            print(f"❌ Missing environment variables: {missing}")
            return False

        # Try to initialize bot
        bot = DocZapBot()
        print("✅ Bot initialized successfully")

        # Test authentication service
        auth_result = bot.auth_service.is_authenticated("test_user")
        print(f"✅ Auth service working: {auth_result}")

        # Test AI service
        ai_service_healthy = hasattr(bot.ai_service, 'process_consultation_direct')
        print(f"✅ AI service has direct processing: {ai_service_healthy}")

        # Test default patient
        default_patient = bot.message_handlers.default_patient
        print(f"✅ Default patient configured: {default_patient['full_name']}")

        return True

    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run test"""
    print("🧪 Testing DocZap Bot Simplified Workflow\n")

    success = await test_bot_initialization()

    print(f"\n{'🎉 All tests passed!' if success else '⚠️ Some tests failed.'}")

if __name__ == "__main__":
    asyncio.run(main())