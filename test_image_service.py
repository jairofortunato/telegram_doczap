#!/usr/bin/env python3
"""
Test script to verify image service integration before Railway deployment
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test all imports work correctly"""
    print("\n🧪 Testing imports...")
    try:
        from services.image_service import ImageProcessingService
        print("  ✅ ImageProcessingService imported")

        from services.auth_service import AuthService
        print("  ✅ AuthService imported")

        from services.ai_service import AIService
        print("  ✅ AIService imported")

        from services.whatsapp_service import WhatsAppService
        print("  ✅ WhatsAppService imported")

        from handlers.whatsapp_handler import WhatsAppHandler
        print("  ✅ WhatsAppHandler imported")

        import openai
        print("  ✅ openai imported")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test required environment variables"""
    print("\n🧪 Testing environment variables...")

    required_vars = {
        'OPENAI_API_KEY': 'OpenAI Vision API',
        'SUPABASE_URL': 'Database',
        'SUPABASE_SERVICE_ROLE_KEY': 'Database auth',
        'TELEGRAM_BOT_TOKEN': 'Telegram bot'
    }

    missing = []
    for var, purpose in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show first/last 4 chars for security
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"  ✅ {var}: {masked} ({purpose})")
        else:
            print(f"  ❌ {var}: Missing ({purpose})")
            missing.append(var)

    if missing:
        print(f"\n  ⚠️  Missing variables: {', '.join(missing)}")
        return False

    return True

def test_image_service_initialization():
    """Test ImageProcessingService can initialize"""
    print("\n🧪 Testing ImageProcessingService initialization...")

    try:
        from services.image_service import ImageProcessingService

        service = ImageProcessingService()
        print("  ✅ ImageProcessingService initialized")

        # Check attributes
        if hasattr(service, 'client'):
            print("  ✅ OpenAI client available")

        if hasattr(service, 'supabase'):
            print("  ✅ Supabase client available")

        if hasattr(service, 'model'):
            print(f"  ✅ Model: {service.model}")

        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_whatsapp_handler_with_image_service():
    """Test WhatsAppHandler accepts image_service parameter"""
    print("\n🧪 Testing WhatsAppHandler with image_service...")

    try:
        from handlers.whatsapp_handler import WhatsAppHandler
        from services.image_service import ImageProcessingService

        # Create mock services
        image_service = ImageProcessingService()

        # Try to create handler with image_service
        handler = WhatsAppHandler(
            whatsapp_service=None,  # Mock
            auth_service=None,  # Mock
            ai_service=None,  # Mock
            subscription_service=None,
            processing_state=None,
            image_service=image_service
        )

        print("  ✅ WhatsAppHandler accepts image_service")

        if hasattr(handler, 'image_service'):
            print("  ✅ image_service attribute exists")

        if hasattr(handler, 'handle_image_message'):
            print("  ✅ handle_image_message method exists")

        return True
    except Exception as e:
        print(f"  ❌ Handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🧪 Testing OpenAI API connection...")

    try:
        import openai
        from services.image_service import ImageProcessingService

        service = ImageProcessingService()

        # Try a simple API call (this will cost ~$0.0001)
        print("  🔄 Making test API call to OpenAI...")
        import asyncio

        async def test_call():
            try:
                messages = [
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Respond with 'OK' if you receive this."}
                ]

                response = await service.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=10
                )

                return response.choices[0].message.content
            except Exception as e:
                return f"Error: {e}"

        result = asyncio.run(test_call())

        if "Error" not in result:
            print(f"  ✅ OpenAI API connected: {result}")
            return True
        else:
            print(f"  ❌ OpenAI API error: {result}")
            return False

    except Exception as e:
        print(f"  ❌ OpenAI connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_py_structure():
    """Test main.py can be imported"""
    print("\n🧪 Testing main.py structure...")

    try:
        # Add current directory to path
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Try importing main (this will initialize services)
        print("  🔄 Importing main module...")
        import main

        print("  ✅ main.py imported successfully")

        # Check key components
        if hasattr(main, 'app'):
            print("  ✅ FastAPI app exists")

        if hasattr(main, 'image_service'):
            print("  ✅ image_service exists in main")

        if hasattr(main, 'whatsapp_handler'):
            print("  ✅ whatsapp_handler exists in main")

        return True
    except Exception as e:
        print(f"  ❌ main.py import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("🚀 Railway Deployment Pre-Check - Image Service Integration")
    print("=" * 70)

    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("ImageProcessingService Init", test_image_service_initialization),
        ("WhatsAppHandler Integration", test_whatsapp_handler_with_image_service),
        ("Main.py Structure", test_main_py_structure),
    ]

    # Optional OpenAI test (costs money) - Disabled in non-interactive mode
    try:
        test_openai = input("\n💰 Test OpenAI API connection? (costs ~$0.0001) [y/N]: ").lower() == 'y'
    except (EOFError, KeyboardInterrupt):
        print("\n⏭️  Skipping OpenAI API test (non-interactive mode)")
        test_openai = False

    if test_openai:
        tests.append(("OpenAI API Connection", test_openai_connection))

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("=" * 70)
    print(f"\n🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Safe to deploy to Railway")
        print("\nNext steps:")
        print("  1. git add .")
        print("  2. git commit -m 'Add image processing feature'")
        print("  3. railway up")
        print("  4. railway logs --tail")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("❌ Fix issues before deploying to Railway")
        print("\nCheck the errors above and:")
        print("  1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("  2. Check .env file has all required variables")
        print("  3. Verify OPENAI_API_KEY is valid")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
