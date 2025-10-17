#!/usr/bin/env python3
"""
Test script for DocZap Telegram Bot integration with AI Processor
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ai_processor_health():
    """Test if AI processor is reachable"""
    ai_url = os.getenv('AI_PROCESSOR_URL')
    if not ai_url:
        print("❌ AI_PROCESSOR_URL not configured")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ai_url}/health")
            if response.status_code == 200:
                print(f"✅ AI Processor health check passed: {ai_url}")
                return True
            else:
                print(f"❌ AI Processor health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Failed to connect to AI Processor: {e}")
        return False

async def test_telegram_endpoint():
    """Test if Telegram-specific endpoint exists"""
    ai_url = os.getenv('AI_PROCESSOR_URL')
    if not ai_url:
        print("❌ AI_PROCESSOR_URL not configured")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ai_url}/api/doctor/health")
            if response.status_code == 200:
                print(f"✅ Telegram endpoint health check passed")
                return True
            else:
                print(f"❌ Telegram endpoint health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Failed to connect to Telegram endpoint: {e}")
        return False

async def test_bot_configuration():
    """Test bot configuration"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'AI_PROCESSOR_URL'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    else:
        print(f"✅ All required environment variables configured")
        return True

async def main():
    """Run all tests"""
    print("🧪 Testing DocZap Telegram Bot Integration\n")

    tests = [
        ("Bot Configuration", test_bot_configuration),
        ("AI Processor Health", test_ai_processor_health),
        ("Telegram Endpoint", test_telegram_endpoint)
    ]

    results = []
    for name, test_func in tests:
        print(f"🔍 Testing {name}...")
        result = await test_func()
        results.append((name, result))
        print()

    print("📋 Test Summary:")
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! Bot is ready for deployment.")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues before deploying.")

if __name__ == "__main__":
    asyncio.run(main())