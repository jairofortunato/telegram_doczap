# Development Testing Guide - DocZap Bot

This guide explains how to safely test the telegram-doczap bot locally before deploying to production.

## Overview

The bot is a **webhook-based** FastAPI application. For development testing, you have several options to test changes before shipping to production.

## Testing Strategies

### Strategy 1: Local Development with ngrok (Recommended)

This approach lets you test the full webhook flow locally.

#### Setup Steps

1. **Install ngrok**:
   ```bash
   # macOS
   brew install ngrok

   # Or download from https://ngrok.com/download
   ```

2. **Start your local bot**:
   ```bash
   cd telegram-doczap

   # Activate virtual environment
   source venv/bin/activate

   # Run the bot locally
   python main.py
   ```

   The bot will start on `http://localhost:8000`

3. **Expose local server with ngrok**:
   ```bash
   # In a new terminal
   ngrok http 8000
   ```

   You'll get a URL like: `https://abc123.ngrok.io`

4. **Set Telegram webhook to ngrok URL**:
   ```bash
   # Replace YOUR_BOT_TOKEN and YOUR_NGROK_URL
   curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://YOUR_NGROK_URL.ngrok.io/telegram/webhook"}'
   ```

5. **Test with your Telegram bot**:
   - Open Telegram and find your bot
   - Send `/start` command
   - Test voice messages, login, etc.
   - Watch logs in your terminal

6. **When done testing, remove webhook**:
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/deleteWebhook"
   ```

**Pros**: Full production-like testing
**Cons**: Requires ngrok, webhook setup

---

### Strategy 2: Create a Test Bot

Create a separate test bot for development to avoid disrupting production users.

#### Setup Steps

1. **Create a new test bot**:
   - Open Telegram and talk to `@BotFather`
   - Send `/newbot`
   - Name it: `DocZap Test Bot`
   - Username: `doczap_test_bot`
   - Save the token

2. **Configure test environment**:
   ```bash
   # Create .env.test file
   cp .env .env.test

   # Edit .env.test with your test bot token
   # TELEGRAM_BOT_TOKEN=your_test_bot_token_here
   ```

3. **Load test environment and run**:
   ```bash
   # Load test environment
   export $(cat .env.test | xargs)

   # Start bot with ngrok (Strategy 1)
   python main.py
   ```

4. **Set webhook for test bot** (using ngrok from Strategy 1)

5. **Test freely without affecting production**

**Pros**: Safe isolated testing
**Cons**: Requires separate bot token, still needs ngrok

---

### Strategy 3: Manual API Testing

Test individual endpoints without setting up webhooks.

#### Testing Authentication Flow

```bash
cd telegram-doczap

# Test doctor authentication
python -c "
import asyncio
from services.auth_service import AuthService

async def test():
    auth = AuthService()
    result = await auth.authenticate_doctor(
        user_id=12345,
        email='doctor@example.com',
        password='your_password'
    )
    print('Auth result:', result)

asyncio.run(test())
"
```

#### Testing AI Service

```bash
# Test AI service with a sample audio file
python -c "
import asyncio
from services.ai_service import AIService

async def test():
    ai = AIService()

    # Create test patient data
    patient = {
        'full_name': 'Test Patient',
        'cpf': '00000000000',
        'pin': '0000'
    }

    # Test with your audio file
    result = await ai.process_consultation_direct(
        audio_file_path='/path/to/test/audio.ogg',
        patient_data=patient,
        doctor_session={'profile_id': 'test-id'},
        template={'name': 'SOAP padrão'}
    )

    print('AI result:', result)

asyncio.run(test())
"
```

#### Test Health Endpoint

```bash
# Start the server
python main.py

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/processing-stats
```

**Pros**: No webhook setup needed
**Cons**: Doesn't test full Telegram integration

---

### Strategy 4: Mock Webhook Requests

Simulate Telegram webhook calls locally without ngrok.

Create a test script `test_webhook_local.py`:

```python
#!/usr/bin/env python3
"""
Local webhook testing script - simulates Telegram sending updates
"""

import httpx
import asyncio
import json

async def test_start_command():
    """Test /start command"""
    webhook_data = {
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 12345,
                "type": "private"
            },
            "text": "/start",
            "date": 1234567890
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/telegram/webhook",
            json=webhook_data
        )
        print(f"Start command response: {response.status_code}")
        print(f"Response: {response.json()}")

async def test_login_flow():
    """Test email/password login"""
    # Send email
    email_data = {
        "message": {
            "message_id": 2,
            "from": {"id": 12345, "first_name": "Test"},
            "chat": {"id": 12345, "type": "private"},
            "text": "doctor@example.com",
            "date": 1234567890
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/telegram/webhook",
            json=email_data
        )
        print(f"Email response: {response.json()}")

    # Send password
    password_data = {
        "message": {
            "message_id": 3,
            "from": {"id": 12345, "first_name": "Test"},
            "chat": {"id": 12345, "type": "private"},
            "text": "your_password",
            "date": 1234567891
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/telegram/webhook",
            json=password_data
        )
        print(f"Password response: {response.json()}")

async def main():
    print("🧪 Testing webhook endpoints locally...\n")

    print("1. Testing /start command...")
    await test_start_command()

    print("\n2. Testing login flow...")
    await test_login_flow()

    print("\n✅ Tests complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

**Usage**:
```bash
# Terminal 1: Start bot
python main.py

# Terminal 2: Run tests
python test_webhook_local.py
```

**Pros**: No external dependencies, fast iteration
**Cons**: Doesn't test actual Telegram integration, manual mock data creation

---

### Strategy 5: Use Existing Test Scripts

The project already has test files you can use:

```bash
cd telegram-doczap

# Simple bot initialization test
python test_bot_simple.py

# Full integration test
python test_integration.py

# Basic bot test
python test_bot.py
```

Update these test files to match your current bot structure.

---

## Recommended Development Workflow

### For Quick Changes (UI/Logic)

```bash
# 1. Make your changes
vim handlers/whatsapp_handler.py

# 2. Run local tests
python test_webhook_local.py

# 3. Test with ngrok if needed
ngrok http 8000
# Set webhook to ngrok URL
# Test manually in Telegram
```

### For AI/Audio Changes

```bash
# 1. Test AI service directly
python -c "from services.ai_service import AIService; ..."

# 2. Test with a sample audio file
# Create test_audio_processing.py
python test_audio_processing.py

# 3. Test full flow with ngrok + test bot
```

### Before Production Deploy

```bash
# 1. Run all test scripts
python test_bot_simple.py
python test_integration.py
python test_webhook_local.py

# 2. Test with test bot using ngrok
# Verify all commands work:
# - /start
# - /login
# - /status
# - /templates
# - Voice message processing

# 3. Check logs for errors
# Watch terminal output

# 4. Test WhatsApp if enabled
# Send test messages to WhatsApp number

# 5. Deploy to Railway
railway up

# 6. Set production webhook
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-railway-url.up.railway.app/telegram/webhook"}'
```

---

## Environment Variables for Testing

Create different environment files for different stages:

```bash
# .env.local - Local development
TELEGRAM_BOT_TOKEN=test_bot_token
AI_PROCESSOR_URL=http://localhost:8000
SUPABASE_URL=https://your-project.supabase.co

# .env.staging - Test bot with production services
TELEGRAM_BOT_TOKEN=test_bot_token
AI_PROCESSOR_URL=https://saude-ai-processor-production-bebd.up.railway.app
SUPABASE_URL=https://your-project.supabase.co

# .env.production - Production (Railway)
TELEGRAM_BOT_TOKEN=production_bot_token
AI_PROCESSOR_URL=https://saude-ai-processor-production-bebd.up.railway.app
SUPABASE_URL=https://your-project.supabase.co
```

---

## Debugging Tips

### Enable Detailed Logging

```python
# Add to main.py for development
import logging
logging.basicConfig(level=logging.DEBUG)

# Or configure loguru for more details
from loguru import logger
logger.add("debug.log", level="DEBUG", rotation="10 MB")
```

### Check Webhook Status

```bash
# Get current webhook info
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

### Monitor ngrok Traffic

When using ngrok, visit `http://localhost:4040` to see:
- All HTTP requests
- Request/response bodies
- Timing information

### Test Database Connection

```bash
python -c "
from services.auth_service import AuthService
import asyncio

async def test_db():
    auth = AuthService()
    # This will test Supabase connection
    print('Supabase client:', auth.supabase)

asyncio.run(test_db())
"
```

---

## Common Issues and Solutions

### Issue: Webhook not receiving updates

**Solution**:
```bash
# Check webhook status
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"

# Delete old webhook
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/deleteWebhook"

# Set new webhook
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -d "url=https://your-ngrok-url.ngrok.io/telegram/webhook"
```

### Issue: ngrok session expired

**Solution**: Free ngrok sessions expire after 2 hours. Restart ngrok and update webhook URL.

### Issue: Module import errors

**Solution**:
```bash
# Make sure you're in the venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Audio processing fails

**Solution**: Check AI processor is running:
```bash
curl https://saude-ai-processor-production-bebd.up.railway.app/health
```

---

## Safety Checklist Before Deploy

- [ ] All test scripts pass
- [ ] Tested with test bot using ngrok
- [ ] Verified authentication works
- [ ] Tested voice message processing
- [ ] Checked template selection
- [ ] Reviewed logs for errors
- [ ] Environment variables set correctly
- [ ] Webhook URL points to production (Railway)
- [ ] Test bot webhook removed
- [ ] Production bot webhook set

---

## Quick Reference Commands

```bash
# Start local development
python main.py

# Expose with ngrok
ngrok http 8000

# Set webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" -d "url=<URL>/telegram/webhook"

# Check webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Delete webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# Deploy to Railway
railway up

# Check Railway logs
railway logs
```

---

## Testing Checklist

### Unit Testing
- [ ] Authentication service
- [ ] AI service connection
- [ ] WhatsApp service (if enabled)
- [ ] Template fetching
- [ ] Error handling

### Integration Testing
- [ ] /start command
- [ ] Login flow (email → password)
- [ ] /status command
- [ ] /templates command
- [ ] /template selection
- [ ] Voice message processing
- [ ] /logout command
- [ ] /help command
- [ ] /debug command

### End-to-End Testing
- [ ] Full doctor workflow
- [ ] Multiple users simultaneously
- [ ] Large audio files
- [ ] Error scenarios (wrong password, invalid audio)
- [ ] Template switching
- [ ] Session persistence

---

## Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [ngrok Documentation](https://ngrok.com/docs)
- [Railway Deployment Guide](https://docs.railway.app/)

---

## Getting Help

If you encounter issues:

1. Check the logs: `tail -f debug.log`
2. Verify environment variables: `env | grep TELEGRAM`
3. Test individual services (auth, AI, DB)
4. Use `/debug` command in Telegram
5. Check Railway deployment logs: `railway logs`
