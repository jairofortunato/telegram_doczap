# Quick Start Testing Guide

This is a condensed guide to get you testing the telegram-doczap bot quickly.

## Method 1: Local Testing Without Telegram (Fastest)

Test the bot's endpoints locally without needing ngrok or a Telegram bot:

```bash
# Terminal 1: Start the bot
cd telegram-doczap
source venv/bin/activate
python main.py

# Terminal 2: Run automated tests
cd telegram-doczap
source venv/bin/activate
python test_webhook_local.py
```

The test script will:
- Test all bot commands (/start, /help, /status, /logout)
- Verify health endpoints
- Check processing stats
- Validate WhatsApp webhook

**When to use**: Quick iterations, testing logic changes, debugging

---

## Method 2: Full Integration Testing with ngrok (Recommended)

Test with real Telegram messages:

```bash
# Terminal 1: Start the bot
cd telegram-doczap
source venv/bin/activate
python main.py

# Terminal 2: Start ngrok
ngrok http 8000

# Terminal 3: Set webhook
export BOT_TOKEN="your_bot_token_here"
export NGROK_URL="https://abc123.ngrok.io"  # From ngrok output

curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${NGROK_URL}/telegram/webhook\"}"

# Verify webhook is set
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

# Now test in Telegram app!
# Open your bot and send: /start
```

**When to use**: Testing before deployment, end-to-end testing

---

## Method 3: Use a Test Bot (Safest for Production)

Create a separate bot for development:

```bash
# 1. Create test bot with @BotFather in Telegram
#    Name: DocZap Test
#    Username: doczap_test_bot

# 2. Create test environment
cd telegram-doczap
cp .env .env.test

# 3. Edit .env.test with test bot token
# TELEGRAM_BOT_TOKEN=your_test_bot_token

# 4. Start bot with test environment
export $(cat .env.test | xargs)
python main.py

# 5. Use ngrok + webhook (Method 2)
# 6. Test freely without affecting production users
```

**When to use**: Testing with production services, avoiding disruption

---

## Debugging Checklist

If something doesn't work:

```bash
# 1. Check bot is running
curl http://localhost:8000/health

# 2. Check environment variables
echo $TELEGRAM_BOT_TOKEN
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TELEGRAM_BOT_TOKEN'))"

# 3. Check webhook status
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

# 4. Remove old webhook if needed
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"

# 5. Check ngrok is running (if using)
curl http://localhost:4040/api/tunnels

# 6. Test database connection
python -c "
from services.auth_service import AuthService
auth = AuthService()
print('Supabase client:', auth.supabase)
"

# 7. Test AI processor connection
curl https://saude-ai-processor-production-bebd.up.railway.app/health
```

---

## Common Testing Workflows

### Testing a Quick Fix
```bash
# 1. Make your change
vim services/auth_service.py

# 2. Restart bot
# Ctrl+C in terminal, then:
python main.py

# 3. Run quick test
python test_webhook_local.py
```

### Testing Voice Processing
```bash
# 1. Start bot with ngrok (Method 2)
# 2. In Telegram, send /start then /login
# 3. Record and send a voice message
# 4. Watch logs in terminal
# 5. Check response in Telegram
```

### Testing Before Deploy
```bash
# 1. Run all automated tests
python test_webhook_local.py

# 2. Test with real Telegram (ngrok)
# 3. Test all commands: /start, /login, /status, /templates
# 4. Test voice message
# 5. Test error scenarios (wrong password, etc.)
# 6. Check logs for errors
# 7. Ready to deploy!
```

---

## Deploy to Production

When tests pass:

```bash
# 1. Commit changes (if in git repo)
git add .
git commit -m "Your changes"
git push

# 2. Deploy to Railway
railway up

# 3. Set production webhook
export PROD_URL="https://your-app.up.railway.app"
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=${PROD_URL}/telegram/webhook"

# 4. Verify
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

# 5. Test in production
# Send /start to your production bot

# 6. Monitor logs
railway logs --tail
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python main.py` | Start bot locally |
| `ngrok http 8000` | Expose local server |
| `python test_webhook_local.py` | Run automated tests |
| `curl localhost:8000/health` | Check bot health |
| `railway up` | Deploy to Railway |
| `railway logs` | View Railway logs |

---

## Environment Variables Needed

Minimum for local testing:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key
AI_PROCESSOR_URL=https://saude-ai-processor-production-bebd.up.railway.app
```

Optional:
```env
WHATSAPP_ACCESS_TOKEN=your_token  # For WhatsApp testing
PORT=8000  # Default port
```

---

## Help & Resources

- **Full Testing Guide**: See `DEVELOPMENT_TESTING.md`
- **Implementation Guide**: See `IMPLEMENTATION-GUIDE.md`
- **Main README**: See `README.md`
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **ngrok Docs**: https://ngrok.com/docs

---

## Pro Tips

1. **Use test bot for development** - Avoid disrupting production users
2. **Keep ngrok running** - Free tier sessions last 2 hours
3. **Monitor ngrok dashboard** - Visit http://localhost:4040 to see all requests
4. **Check logs first** - Most issues show up in bot logs
5. **Test incrementally** - Test each change before moving to next
6. **Use /debug command** - Built-in debugging in Telegram
7. **Webhook vs Polling** - This bot uses webhooks (requires ngrok for local testing)

---

## Need More Help?

Run the automated test suite:
```bash
python test_webhook_local.py
```

Check detailed testing guide:
```bash
cat DEVELOPMENT_TESTING.md
```

Check webhook status:
```bash
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

Happy testing! 🚀
