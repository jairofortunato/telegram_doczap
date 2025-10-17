#!/usr/bin/env python3
"""
Script to generate permanent WhatsApp Business API access token using Graph API
"""

import os
import requests
import json
from datetime import datetime, timedelta

def get_app_credentials():
    """Get app credentials from environment or user input"""
    app_id = os.getenv('WHATSAPP_APP_ID') or input("Enter your WhatsApp App ID: ")
    app_secret = os.getenv('WHATSAPP_APP_SECRET') or input("Enter your WhatsApp App Secret: ")
    current_token = os.getenv('WHATSAPP_ACCESS_TOKEN') or input("Enter your current temporary access token: ")

    return app_id, app_secret, current_token

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

def get_permanent_token_system_user(app_id, long_lived_token):
    """Generate permanent token using System User (if available)"""

    print("\n🔄 Attempting to generate permanent token via System User...")

    # First, get business accounts
    url = f"https://graph.facebook.com/v18.0/{app_id}/accounts"

    headers = {
        'Authorization': f'Bearer {long_lived_token}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(f"📊 Business accounts response: {json.dumps(data, indent=2)}")

        # Look for business accounts that can generate permanent tokens
        if 'data' in data and data['data']:
            for account in data['data']:
                account_id = account.get('id')

                # Try to generate permanent token for this account
                token_url = f"https://graph.facebook.com/v18.0/{account_id}/access_tokens"

                token_response = requests.post(token_url, headers=headers)

                if token_response.status_code == 200:
                    token_data = token_response.json()
                    print(f"🎯 Permanent token data: {json.dumps(token_data, indent=2)}")

                    if 'data' in token_data and token_data['data']:
                        permanent_token = token_data['data'][0].get('access_token')
                        if permanent_token:
                            print("✅ Successfully generated permanent token!")
                            return permanent_token

        print("⚠️  No permanent token available via System User method")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating permanent token: {e}")
        return None

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

        # Get token debug info
        debug_url = "https://graph.facebook.com/v18.0/debug_token"
        debug_params = {
            'input_token': token,
            'access_token': token
        }

        debug_response = requests.get(debug_url, params=debug_params)
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"🔍 Token debug info: {json.dumps(debug_data, indent=2)}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Token verification failed: {e}")
        return False

def save_token_to_env_file(token, expiration_date=None):
    """Save token to .env file"""

    env_file_path = "/Users/jairofortunato/Desktop/Desktop2/saudenobolso/telegram-doczap/.env"

    try:
        # Read current .env file
        with open(env_file_path, 'r') as f:
            lines = f.readlines()

        # Update or add WHATSAPP_ACCESS_TOKEN
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('WHATSAPP_ACCESS_TOKEN='):
                lines[i] = f'WHATSAPP_ACCESS_TOKEN={token}\n'
                updated = True
                break

        if not updated:
            lines.append(f'WHATSAPP_ACCESS_TOKEN={token}\n')

        # Add expiration comment
        if expiration_date:
            expiration_comment = f'# Token expires on: {expiration_date.strftime("%Y-%m-%d %H:%M:%S")}\n'
            if not any('Token expires on:' in line for line in lines):
                lines.insert(-1, expiration_comment)

        # Write back to file
        with open(env_file_path, 'w') as f:
            f.writelines(lines)

        print(f"✅ Token saved to {env_file_path}")

    except Exception as e:
        print(f"❌ Error saving token to .env file: {e}")
        print(f"📝 Please manually add this to your .env file:")
        print(f"WHATSAPP_ACCESS_TOKEN={token}")

def main():
    """Main function to generate permanent token"""

    print("🚀 WhatsApp Business API - Permanent Token Generator")
    print("="*50)

    # Get credentials
    app_id, app_secret, current_token = get_app_credentials()

    print(f"\n📱 App ID: {app_id}")
    print(f"🔑 Current token: {current_token[:20]}...")

    # Verify current token
    print("\n🔍 Verifying current token...")
    if not verify_token(current_token):
        print("❌ Current token is invalid. Please check your token.")
        return

    # Exchange for long-lived token
    long_lived_token, expiration_date = exchange_for_long_lived_token(app_id, app_secret, current_token)

    if not long_lived_token:
        print("❌ Failed to generate long-lived token")
        return

    print(f"\n🎯 Long-lived token: {long_lived_token[:20]}...")

    # Try to get permanent token via System User
    permanent_token = get_permanent_token_system_user(app_id, long_lived_token)

    # Use the best token available
    final_token = permanent_token if permanent_token else long_lived_token
    token_type = "permanent" if permanent_token else "long-lived (60 days)"

    print(f"\n🎉 Final token type: {token_type}")
    print(f"🔑 Final token: {final_token[:20]}...")

    # Verify final token
    print(f"\n🔍 Verifying final token...")
    if verify_token(final_token):
        # Save to .env file
        save_token_to_env_file(final_token, expiration_date if not permanent_token else None)

        print(f"\n🎯 SUCCESS! Your {token_type} token is ready.")

        if not permanent_token:
            print(f"⚠️  IMPORTANT: This token expires on {expiration_date.strftime('%Y-%m-%d')}")
            print("📅 Set a reminder to refresh it before expiration.")

        print("\n📋 Next steps:")
        print("1. Restart your application to use the new token")
        print("2. Test WhatsApp functionality")
        print("3. Monitor token expiration (if applicable)")

    else:
        print("❌ Final token verification failed")

if __name__ == "__main__":
    main()