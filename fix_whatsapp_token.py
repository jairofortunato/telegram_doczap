#!/usr/bin/env python3
"""
Quick fix to generate long-lived WhatsApp token for production
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_long_lived_token():
    """Generate a long-lived WhatsApp Business API token"""

    # Get credentials from environment
    app_id = os.getenv('WHATSAPP_APP_ID')
    app_secret = os.getenv('WHATSAPP_APP_SECRET')
    current_token = os.getenv('WHATSAPP_ACCESS_TOKEN')

    print("🔧 WhatsApp Token Fix - Generating Long-lived Token")
    print("=" * 55)

    if not all([app_id, app_secret, current_token]):
        print("❌ Missing environment variables:")
        if not app_id: print("   - WHATSAPP_APP_ID")
        if not app_secret: print("   - WHATSAPP_APP_SECRET")
        if not current_token: print("   - WHATSAPP_ACCESS_TOKEN")
        return

    print(f"📱 App ID: {app_id}")
    print(f"🔐 App Secret: {app_secret[:8]}...")
    print(f"🎫 Current Token: {current_token[:20]}...")
    print()

    # Exchange for long-lived token
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': current_token
    }

    print("🔄 Exchanging for long-lived token...")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if 'access_token' in data:
            new_token = data['access_token']
            expires_in = data.get('expires_in', 'Unknown')

            print("✅ SUCCESS! New long-lived token generated!")
            print(f"🎫 New Token: {new_token}")
            print(f"⏰ Expires in: {expires_in} seconds (~60 days)")
            print()
            print("🔧 Next steps:")
            print("1. Copy the new token above")
            print("2. Update your .env file with the new WHATSAPP_ACCESS_TOKEN")
            print("3. Deploy to production")
            print("4. Test messaging")

            # Optionally update .env file
            update = input("\n🤔 Update .env file automatically? (y/n): ").lower()
            if update == 'y':
                update_env_file(new_token)
        else:
            print("❌ Error: No access token in response")
            print(f"Response: {data}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def update_env_file(new_token):
    """Update the .env file with the new token"""
    try:
        # Read current .env file
        with open('.env', 'r') as f:
            lines = f.readlines()

        # Update the token line
        updated_lines = []
        token_updated = False

        for line in lines:
            if line.startswith('WHATSAPP_ACCESS_TOKEN='):
                updated_lines.append(f'WHATSAPP_ACCESS_TOKEN={new_token}\n')
                token_updated = True
            else:
                updated_lines.append(line)

        # If token line wasn't found, add it
        if not token_updated:
            updated_lines.append(f'WHATSAPP_ACCESS_TOKEN={new_token}\n')

        # Write back to .env file
        with open('.env', 'w') as f:
            f.writelines(updated_lines)

        print("✅ .env file updated successfully!")
        print("📋 Remember to deploy the updated environment variables to production")

    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        print("Please update manually.")

if __name__ == "__main__":
    generate_long_lived_token()