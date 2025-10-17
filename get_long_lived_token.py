#!/usr/bin/env python3
"""
Alternative method to get long-lived WhatsApp Business API token
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def try_different_app_info():
    """Try getting app info with different endpoints"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')

    endpoints_to_try = [
        f"https://graph.facebook.com/v18.0/122238760352162774",
        f"https://graph.facebook.com/v18.0/me",
        f"https://graph.facebook.com/v18.0/app"
    ]

    headers = {'Authorization': f'Bearer {token}'}

    for endpoint in endpoints_to_try:
        try:
            print(f"🔍 Trying endpoint: {endpoint}")
            response = requests.get(endpoint, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
                return data
            else:
                print(f"❌ Failed with status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Error: {e}")

    return None

def get_business_account_info():
    """Get information about the business account that might help with token generation"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')

    headers = {'Authorization': f'Bearer {token}'}

    # Try to get business account with more details
    url = f"https://graph.facebook.com/v18.0/{business_account_id}"
    params = {
        'fields': 'id,name,business_verification_status,owned_whatsapp_business_accounts'
    }

    try:
        print(f"🏢 Getting detailed business account info...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Business account details: {json.dumps(data, indent=2)}")

        return data

    except Exception as e:
        print(f"❌ Error getting business account info: {e}")
        return None

def try_system_user_approach():
    """Try to use system user approach for permanent token"""

    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')

    headers = {'Authorization': f'Bearer {token}'}

    # Try to access system users for this business account
    url = f"https://graph.facebook.com/v18.0/{business_account_id}/system_users"

    try:
        print(f"👤 Checking system users...")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ System users: {json.dumps(data, indent=2)}")

            # If we have system users, try to generate token for them
            if data.get('data'):
                for user in data['data']:
                    user_id = user.get('id')
                    print(f"🔄 Trying to generate token for system user {user_id}...")

                    token_url = f"https://graph.facebook.com/v18.0/{user_id}/access_tokens"
                    token_response = requests.post(token_url, headers=headers)

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        print(f"🎯 Got token data: {json.dumps(token_data, indent=2)}")
                        return token_data
                    else:
                        print(f"❌ Token generation failed: {token_response.text}")

            return data
        else:
            print(f"❌ System users request failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error with system user approach: {e}")
        return None

def check_app_settings():
    """Check if there are issues with app configuration"""

    print("🔧 App Configuration Check:")
    print(f"📱 App ID: {os.getenv('WHATSAPP_APP_SECRET', 'Not found')[:10]}...")
    print(f"🔐 App Secret: {'*' * 20}...{os.getenv('WHATSAPP_APP_SECRET', 'Not found')[-4:]}")
    print(f"🏢 Business Account: {os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', 'Not found')}")
    print(f"📞 Phone Number ID: {os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'Not found')}")

    # Check if we can at least verify the current token is working
    token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}

    try:
        url = "https://graph.facebook.com/v18.0/debug_token"
        params = {
            'input_token': token,
            'access_token': token
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            debug_data = response.json()
            print(f"🔍 Current token debug info: {json.dumps(debug_data, indent=2)}")
            return debug_data
        else:
            print(f"❌ Token debug failed: {response.text}")

    except Exception as e:
        print(f"❌ Error checking token: {e}")

    return None

def main():
    """Try different approaches to get a long-lived token"""

    print("🚀 Alternative Long-Lived Token Generator")
    print("=" * 60)

    # First, let's understand what we're working with
    print("\n1️⃣ Checking current app configuration...")
    check_app_settings()

    print("\n2️⃣ Trying different app info endpoints...")
    try_different_app_info()

    print("\n3️⃣ Getting detailed business account info...")
    get_business_account_info()

    print("\n4️⃣ Trying system user approach...")
    try_system_user_approach()

    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    print("1. Your current token works fine for testing")
    print("2. For production, you may need to:")
    print("   a) Complete business verification in Meta Business Manager")
    print("   b) Create a System User with WhatsApp permissions")
    print("   c) Generate a permanent token through System User")
    print("3. Alternative: Set up a cron job to refresh token every 50 days")

    # Practical solution for now
    print("\n💡 PRACTICAL SOLUTION:")
    print("Your current setup will work for production! Just remember to:")
    print("- Refresh the token every ~60 days")
    print("- Set a calendar reminder")
    print("- Use the same process (regenerate in Meta Console)")

if __name__ == "__main__":
    main()