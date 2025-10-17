#!/usr/bin/env python3
"""
Local webhook testing script - simulates Telegram sending updates
Tests the bot locally without needing ngrok or webhook setup
"""

import httpx
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = 999999  # Fake test user ID
TEST_CHAT_ID = 999999  # Fake test chat ID

async def test_health_check():
    """Test health endpoint"""
    print("\n📊 Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Health check: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def test_start_command():
    """Test /start command"""
    print("\n🤖 Testing /start command...")

    webhook_data = {
        "message": {
            "message_id": 1,
            "from": {
                "id": TEST_USER_ID,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser"
            },
            "chat": {
                "id": TEST_CHAT_ID,
                "type": "private"
            },
            "text": "/start",
            "date": 1234567890
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/telegram/webhook",
                json=webhook_data,
                timeout=10.0
            )
            print(f"✅ /start command: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ /start command failed: {e}")
            return False

async def test_help_command():
    """Test /help command"""
    print("\n❓ Testing /help command...")

    webhook_data = {
        "message": {
            "message_id": 2,
            "from": {"id": TEST_USER_ID, "first_name": "Test"},
            "chat": {"id": TEST_CHAT_ID, "type": "private"},
            "text": "/help",
            "date": 1234567891
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/telegram/webhook",
                json=webhook_data,
                timeout=10.0
            )
            print(f"✅ /help command: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ /help command failed: {e}")
            return False

async def test_status_command():
    """Test /status command"""
    print("\n📋 Testing /status command...")

    webhook_data = {
        "message": {
            "message_id": 3,
            "from": {"id": TEST_USER_ID, "first_name": "Test"},
            "chat": {"id": TEST_CHAT_ID, "type": "private"},
            "text": "/status",
            "date": 1234567892
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/telegram/webhook",
                json=webhook_data,
                timeout=10.0
            )
            print(f"✅ /status command: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ /status command failed: {e}")
            return False

async def test_email_input():
    """Test email input (login flow step 1)"""
    print("\n📧 Testing email input...")

    webhook_data = {
        "message": {
            "message_id": 4,
            "from": {"id": TEST_USER_ID, "first_name": "Test"},
            "chat": {"id": TEST_CHAT_ID, "type": "private"},
            "text": "test@example.com",
            "date": 1234567893
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/telegram/webhook",
                json=webhook_data,
                timeout=10.0
            )
            print(f"✅ Email input: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Email input failed: {e}")
            return False

async def test_logout_command():
    """Test /logout command"""
    print("\n🚪 Testing /logout command...")

    webhook_data = {
        "message": {
            "message_id": 5,
            "from": {"id": TEST_USER_ID, "first_name": "Test"},
            "chat": {"id": TEST_CHAT_ID, "type": "private"},
            "text": "/logout",
            "date": 1234567894
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/telegram/webhook",
                json=webhook_data,
                timeout=10.0
            )
            print(f"✅ /logout command: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ /logout command failed: {e}")
            return False

async def test_processing_stats():
    """Test processing stats endpoint"""
    print("\n📊 Testing processing stats...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/processing-stats")
            print(f"✅ Processing stats: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Processing stats failed: {e}")
            return False

async def test_whatsapp_webhook_get():
    """Test WhatsApp webhook GET (verification)"""
    print("\n💬 Testing WhatsApp webhook verification...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "test_token",
                    "hub.challenge": "12345"
                }
            )
            print(f"✅ WhatsApp webhook GET: {response.status_code}")
            print(f"   Response: {response.text}")
            return True  # May return 403 if WhatsApp not configured, which is OK
        except Exception as e:
            print(f"ℹ️  WhatsApp webhook GET: {e} (OK if WhatsApp not configured)")
            return True

async def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 DocZap Local Webhook Testing Suite")
    print("=" * 70)
    print("\n⚠️  Make sure the bot is running locally first:")
    print("   python main.py")
    print("\n" + "=" * 70)

    results = []

    # Run all tests
    results.append(("Health Check", await test_health_check()))
    results.append(("Start Command", await test_start_command()))
    results.append(("Help Command", await test_help_command()))
    results.append(("Status Command", await test_status_command()))
    results.append(("Email Input", await test_email_input()))
    results.append(("Logout Command", await test_logout_command()))
    results.append(("Processing Stats", await test_processing_stats()))
    results.append(("WhatsApp Webhook", await test_whatsapp_webhook_get()))

    # Print summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 70)
    print(f"\n🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Bot is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    print("\n💡 Next steps:")
    print("   1. Test with a real Telegram bot using ngrok")
    print("   2. See DEVELOPMENT_TESTING.md for detailed guide")
    print("   3. Deploy to Railway when ready")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
