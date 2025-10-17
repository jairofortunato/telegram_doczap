#!/usr/bin/env python3
"""
Interactive script to set up WhatsApp Business API permanent token
"""

import requests
import json
from datetime import datetime, timedelta

def exchange_for_long_lived_token(app_id, app_secret, short_lived_token):
    """Exchange short-lived token for long-lived token (60 days)"""

    url = "https://graph.facebook.com/v18.0/oauth/access_token"

    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_lived_token
    }

    print("🔄 Exchanging temporary token for long-lived token...")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if 'access_token' in data:
            long_lived_token = data['access_token']
            expires_in = data.get('expires_in', 5183944)  # Default 60 days

            # Calculate expiration date
            expiration_date = datetime.now() + timedelta(seconds=expires_in)

            print("✅ Successfully generated long-lived token!")
            print(f"📅 Token expires on: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Expires in: {expires_in // 86400} days")

            return long_lived_token, expiration_date
        else:
            print("❌ Error: No access token in response")
            print(f"Response: {data}")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP Error: {e}")
        return None, None
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        return None, None

def verify_token(token):
    """Verify token validity and get token info"""

    url = "https://graph.facebook.com/v18.0/me"

    headers = {
        'Authorization': f'Bearer {token}'
    }

    params = {
        'fields': 'id,name'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Token is valid! App info: {json.dumps(data, indent=2)}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Token verification failed: {e}")
        return False

def save_to_env_file(env_vars):
    """Save WhatsApp variables to .env file"""

    env_file_path = "/Users/jairofortunato/Desktop/Desktop2/saudenobolso/telegram-doczap/.env"

    try:
        # Read current .env file
        with open(env_file_path, 'r') as f:
            lines = f.readlines()

        # Add WhatsApp section if not exists
        whatsapp_section_exists = any('WhatsApp' in line for line in lines)

        if not whatsapp_section_exists:
            lines.append('\n# WhatsApp Business API Configuration\n')

        # Update or add each variable
        for key, value in env_vars.items():
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}\n'
                    updated = True
                    break

            if not updated:
                lines.append(f'{key}={value}\n')

        # Write back to file
        with open(env_file_path, 'w') as f:
            f.writelines(lines)

        print(f"✅ WhatsApp credentials saved to {env_file_path}")

    except Exception as e:
        print(f"❌ Error saving to .env file: {e}")
        print(f"📝 Please manually add these to your .env file:")
        for key, value in env_vars.items():
            print(f"{key}={value}")

def main():
    """Main function"""

    print("🚀 WhatsApp Business API - Token Setup")
    print("="*50)
    print()
    print("You need to get these from Meta Developer Console:")
    print("1. Go to https://developers.facebook.com/apps")
    print("2. Select your WhatsApp app")
    print("3. Go to WhatsApp > API Setup")
    print()

    # Get credentials from user
    print("📋 Please provide the following information:")
    app_id = input("📱 App ID: ").strip()
    app_secret = input("🔐 App Secret: ").strip()
    phone_number_id = input("📞 Phone Number ID: ").strip()
    current_token = input("🎫 Current Access Token: ").strip()
    webhook_verify_token = input("🔗 Webhook Verify Token (create any string): ").strip()

    print(f"\n🔍 Verifying current token...")
    if not verify_token(current_token):
        print("❌ Current token is invalid. Please check your token.")
        return

    # Exchange for long-lived token
    long_lived_token, expiration_date = exchange_for_long_lived_token(app_id, app_secret, current_token)

    if not long_lived_token:
        print("❌ Failed to generate long-lived token")
        return

    print(f"\n🎯 Long-lived token generated successfully!")
    print(f"🔑 Token: {long_lived_token[:20]}...")

    # Prepare environment variables
    env_vars = {
        'WHATSAPP_ACCESS_TOKEN': long_lived_token,
        'WHATSAPP_PHONE_NUMBER_ID': phone_number_id,
        'WHATSAPP_APP_ID': app_id,
        'WHATSAPP_APP_SECRET': app_secret,
        'WHATSAPP_WEBHOOK_VERIFY_TOKEN': webhook_verify_token,
        'WHATSAPP_API_VERSION': 'v18.0'
    }

    # Add expiration comment
    if expiration_date:
        env_vars['# Token expires on'] = expiration_date.strftime('%Y-%m-%d %H:%M:%S')

    # Save to .env file
    save_to_env_file(env_vars)

    print(f"\n🎉 SUCCESS! Your long-lived token is ready.")
    print(f"⚠️  IMPORTANT: This token expires on {expiration_date.strftime('%Y-%m-%d')}")
    print("📅 Set a reminder to refresh it before expiration.")

    print(f"\n📋 Next steps:")
    print("1. Configure webhook URL in Meta Developer Console:")
    print("   https://your-railway-app.up.railway.app/webhook")
    print("2. Test your WhatsApp integration")
    print("3. Deploy to production")

if __name__ == "__main__":
    main()