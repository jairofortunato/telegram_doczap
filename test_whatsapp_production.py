#!/usr/bin/env python3
"""
Test WhatsApp Business API production setup
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_token_validity():
    """Test if the WhatsApp token is valid"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')

    if not token:
        print("❌ WHATSAPP_ACCESS_TOKEN not found in environment")
        return False

    url = "https://graph.facebook.com/v18.0/me"
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        print("🔍 Testing token validity...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Token is valid! App info:")
        print(f"   App ID: {data.get('id', 'N/A')}")
        print(f"   App Name: {data.get('name', 'N/A')}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Token validation failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False

def test_phone_number_access():
    """Test access to WhatsApp phone number"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

    if not phone_number_id:
        print("❌ WHATSAPP_PHONE_NUMBER_ID not found in environment")
        return False

    url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        print(f"📞 Testing phone number access ({phone_number_id})...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Phone number accessible!")
        print(f"   Phone Number: {data.get('display_phone_number', 'N/A')}")
        print(f"   Status: {data.get('verified_name', 'N/A')}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Phone number access failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False

def test_webhook_url():
    """Test if webhook URL is accessible"""

    webhook_url = "https://your-railway-app.up.railway.app/webhook"  # You'll need to update this

    try:
        print(f"🌐 Testing webhook URL accessibility...")
        # Test GET request (webhook verification)
        response = requests.get(webhook_url, timeout=10)

        if response.status_code == 200:
            print(f"✅ Webhook URL is accessible")
        elif response.status_code == 403:
            print(f"⚠️  Webhook URL returns 403 (expected without proper verification params)")
        else:
            print(f"⚠️  Webhook returned status: {response.status_code}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook URL not accessible: {e}")
        return False

def test_business_account_access():
    """Test access to WhatsApp Business Account"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')

    if not business_account_id:
        print("❌ WHATSAPP_BUSINESS_ACCOUNT_ID not found in environment")
        return False

    url = f"https://graph.facebook.com/v18.0/{business_account_id}"
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        print(f"🏢 Testing business account access ({business_account_id})...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Business account accessible!")
        print(f"   Account Name: {data.get('name', 'N/A')}")
        print(f"   Account ID: {data.get('id', 'N/A')}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Business account access failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False

def check_token_expiration():
    """Check token expiration using debug endpoint"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')

    url = "https://graph.facebook.com/v18.0/debug_token"
    params = {
        'input_token': token,
        'access_token': token
    }

    try:
        print("📅 Checking token expiration...")
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        token_data = data.get('data', {})

        expires_at = token_data.get('expires_at')
        if expires_at and expires_at > 0:
            expiration_date = datetime.fromtimestamp(expires_at)
            print(f"⏰ Token expires: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")

            days_left = (expiration_date - datetime.now()).days
            if days_left > 30:
                print(f"✅ Token valid for {days_left} more days")
            elif days_left > 7:
                print(f"⚠️  Token expires in {days_left} days - consider refreshing soon")
            else:
                print(f"🚨 Token expires in {days_left} days - refresh urgently!")
        else:
            print("✅ Token appears to be permanent (no expiration)")

        print(f"🔍 Token scopes: {', '.join(token_data.get('scopes', []))}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Token expiration check failed: {e}")
        return False

def main():
    """Run all production tests"""

    print("🚀 WhatsApp Business API - Production Setup Test")
    print("=" * 60)
    print()

    # Check all environment variables
    required_vars = [
        'WHATSAPP_ACCESS_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID',
        'WHATSAPP_BUSINESS_ACCOUNT_ID',
        'WHATSAPP_APP_SECRET',
        'WEBHOOK_VERIFY_TOKEN'
    ]

    print("🔧 Checking environment variables...")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: Missing")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        return

    print("\n" + "=" * 60)

    # Run tests
    tests = [
        ("Token Validity", test_token_validity),
        ("Phone Number Access", test_phone_number_access),
        ("Business Account Access", test_business_account_access),
        ("Token Expiration", check_token_expiration),
        # ("Webhook URL", test_webhook_url),  # Commented out as it needs actual Railway URL
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)

        if test_func():
            passed += 1

        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 SUCCESS! Your WhatsApp Business API is ready for production!")
        print("\n📋 Next steps:")
        print("1. Update your webhook URL in Meta Developer Console")
        print("2. Deploy your bot to Railway/production")
        print("3. Test end-to-end message flow")
    else:
        print("⚠️  Some tests failed. Please check the configuration above.")

if __name__ == "__main__":
    main()