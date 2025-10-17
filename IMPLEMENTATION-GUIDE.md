# ⚡ DocZap - Telegram Bot Implementation Guide

## 📋 Overview

This Telegram bot provides ProntoDoc functionality, allowing doctors to transcribe medical consultations using Telegram's native audio recording feature. The bot uses Supabase authentication, PostgreSQL database, and Railway-deployed AI processor.

## 🏗️ Architecture

```
Telegram Bot
├── Same Authentication (Supabase)
├── Same Database (PostgreSQL)
├── Railway AI Processor (FastAPI)
└── Native Telegram Audio Recording
```

## 📁 Project Structure

```
telegram-doczap/
├── src/
│   ├── handlers/
│   │   └── messageHandler.js          # Telegram message handling
│   ├── services/
│   │   ├── authService.js             # Doctor authentication
│   │   └── aiService.js               # AI processing & transcription
│   ├── lib/
│   │   └── supabase.js                # Database connection
│   ├── utils/
│   │   └── audioUtils.js              # Audio file handling
│   └── index.js                       # Main bot entry point
├── downloads/                         # Temporary audio files
├── package.json                       # Dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
└── IMPLEMENTATION-GUIDE.md            # This guide
```

## 🚀 Step-by-Step Implementation

### Step 1: Prerequisites

#### 1.1 Required Services
- ✅ **Web App Running**: `web-saude-no-bolso` must be operational
- ✅ **AI Processor Running**: Backend AI service must be active
- ✅ **Supabase Database**: Same database as web app
- 🆕 **Telegram Bot Token**: New bot token from BotFather

#### 1.2 System Requirements
- Node.js 18+
- Access to same Supabase project as web app
- Access to same AI processor as web app

### Step 2: Create Telegram Bot

#### 2.1 Create Bot with BotFather
1. Open Telegram and search for `@BotFather`
2. Send `/start` to BotFather
3. Send `/newbot`
4. Choose bot name: `Saúde no Bolso Bot`
5. Choose username: `saudenobolso_bot` (must end with 'bot')
6. **Save the bot token** - you'll need it for `.env`

#### 2.2 Configure Bot Settings
```bash
# Send to @BotFather:
/setdescription
# Then paste:
Bot médico para transcrição de consultas via áudio. Mesmo sistema do Saúde no Bolso web.

/setabouttext
# Then paste:
🏥 Saúde no Bolso - Transcrição médica via Telegram

/setuserpic
# Upload a medical-themed icon
```

### Step 3: Environment Setup

#### 3.1 Install Dependencies
```bash
cd telegram-bot-saude-no-bolso
npm install
```

#### 3.2 Create Environment File
```bash
cp .env.example .env
```

#### 3.3 Configure Environment Variables
```bash
# Edit .env file with your values:

# Telegram Bot Token (from BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFghijklmnopqrstuvwxyz123456789

# Supabase (SAME as web app)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

# AI Processor (SAME as web app)
AI_PROCESSOR_URL=http://localhost:8000
OPENAI_API_KEY=sk-...

# Optional settings
NODE_ENV=development
PORT=3000
MAX_AUDIO_SIZE_MB=10
SUPPORTED_AUDIO_FORMATS=mp3,ogg,wav,m4a
```

### Step 4: Database Verification

#### 4.1 Ensure Database is Ready
The bot uses the **exact same database** as the web app. Verify:

```sql
-- Check if profiles table exists with required fields
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'profiles';

-- Should include: profile_id, user_id, email, role, cpf, pin, etc.
```

#### 4.2 No Additional Database Setup Required
- ✅ Uses existing `profiles` table
- ✅ Uses existing medical data tables (`medications`, `allergies`, etc.)
- ✅ Uses existing RLS policies
- ✅ No new migrations needed

### Step 5: Start the Bot

#### 5.1 Development Mode
```bash
npm run dev
# This uses nodemon for auto-restart during development
```

#### 5.2 Production Mode
```bash
npm start
# Direct node execution for production
```

#### 5.3 Verify Bot is Running
You should see:
```
🤖 Saúde no Bolso Telegram Bot started successfully!
🎙️ Ready to process medical consultations via voice messages
🏥 Connected to same database as web application
```

### Step 6: Test the Bot

#### 6.1 Find Your Bot
1. Open Telegram
2. Search for your bot username (e.g., `@saudenobolso_bot`)
3. Send `/start`

#### 6.2 Test Authentication
```
/start
/login your.doctor.email@domain.com yourpassword
```

#### 6.3 Test Patient Search
```
/patient 123456
# Or just send: 123456
```

#### 6.4 Test Audio Transcription
1. Select a patient with valid PIN
2. Record a voice message in Telegram
3. Send the voice message to the bot
4. Receive transcription and generated prontuário

### Step 7: Bot Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot and show welcome | `/start` |
| `/login` | Authenticate as doctor | `/login email@domain.com password123` |
| `/patient` | Search patient by PIN | `/patient 123456` |
| `/status` | Show current session info | `/status` |
| `/help` | Show all commands | `/help` |
| `/logout` | End current session | `/logout` |

### Step 8: Usage Workflow

#### 8.1 Doctor Login Flow
```
1. Doctor sends: /login email@domain.com password
2. Bot validates with same Supabase auth as web app
3. Bot stores session in memory
4. Doctor receives confirmation
```

#### 8.2 Consultation Flow
```
1. Doctor sends: /patient 123456
2. Bot searches same database as web app
3. Bot shows patient info and medical history
4. Doctor records voice message (native Telegram audio)
5. Bot downloads audio file
6. Bot sends to same AI processor as web app
7. Bot receives transcription and prontuário
8. Bot saves to same database as web app
9. Doctor receives formatted results
```

### Step 9: Deployment Options

#### 9.1 Local Development
```bash
# Run alongside web app
npm run dev
```

#### 9.2 Server Deployment
```bash
# Using PM2
npm install -g pm2
pm2 start src/index.js --name telegram-bot-saude

# Using Docker
docker build -t telegram-bot-saude .
docker run -d --env-file .env telegram-bot-saude
```

#### 9.3 Cloud Deployment
- **Railway**: Push to GitHub and connect
- **Heroku**: Use Heroku CLI
- **DigitalOcean**: App Platform deployment
- **AWS/GCP**: Container deployment

### Step 10: Security Considerations

#### 10.1 Environment Variables
- ✅ Never commit `.env` to version control
- ✅ Use environment variables in production
- ✅ Rotate bot token periodically

#### 10.2 Authentication Security
- ✅ Login messages are automatically deleted
- ✅ Sessions expire after 24 hours
- ✅ Same security model as web app

#### 10.3 Data Privacy
- ✅ Audio files auto-delete after 1 hour
- ✅ No data stored locally long-term
- ✅ All medical data follows LGPD compliance

### Step 11: Monitoring & Logging

#### 11.1 Bot Logs
```bash
# View logs in development
npm run dev

# View PM2 logs in production
pm2 logs telegram-bot-saude
```

#### 11.2 Health Checks
- Bot responds to `/status` command
- Check active sessions with `/status`
- Monitor AI processor connectivity

#### 11.3 Error Handling
- Graceful error messages to users
- Automatic retry for temporary failures
- Comprehensive logging for debugging

### Step 12: Maintenance

#### 12.1 Regular Tasks
- Monitor disk space (audio files)
- Check bot token validity
- Update dependencies monthly
- Backup configurations

#### 12.2 Updates
- Update web app first
- Update AI processor second
- Update Telegram bot last
- Test full workflow after updates

## 🔧 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Check environment variables
node -e "console.log(process.env.TELEGRAM_BOT_TOKEN)"
```

#### Authentication Failures
```bash
# Test Supabase connection
node -e "
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const client = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
console.log('Supabase connected:', !!client);
"
```

#### AI Processor Issues
```bash
# Test AI processor
curl http://localhost:8000/health
```

#### Audio Download Issues
```bash
# Check downloads directory permissions
ls -la downloads/
mkdir -p downloads
chmod 755 downloads
```

## 📞 Support

### Documentation
- Web App: `/web-saude-no-bolso/docs/`
- AI Processor: `/ai-processor/README.md`
- Database Schema: `/web-saude-no-bolso/database/`

### Key Integration Points
- **Authentication**: Same Supabase Auth as web app
- **Database**: Same PostgreSQL database
- **AI Processing**: Same FastAPI backend
- **User Interface**: Telegram native (voice messages)

## 🎯 Success Metrics

### Working Correctly When:
- ✅ Doctors can login with web app credentials
- ✅ Patient search returns same data as web app
- ✅ Audio transcription works via Telegram voice
- ✅ Prontuários save to same database as web app
- ✅ Generated content matches web app quality

### Integration Verification:
- Test login with existing doctor account
- Search for existing patient from web app
- Verify prontuário appears in web app after bot creation
- Confirm patient data consistency across platforms

The Telegram bot is essentially a **voice-first interface** to the same ProntoDoc system, using Telegram's superior audio recording capabilities while maintaining full feature parity with the web application.