# DocZap - Telegram Bot for Medical Transcription

DocZap is a Telegram bot that enables doctors to transcribe medical consultations through voice messages, integrating with the Saúde no Bolso platform.

## Features

- 🔐 **Doctor Authentication**: Secure login using Supabase credentials
- 👤 **Patient Search**: Find patients by PIN for consultation context
- 🎙️ **Voice Transcription**: Process voice messages and audio files
- 📋 **Medical Records**: Automatic prontuário generation and storage
- 🏥 **Integration**: Full integration with Saúde no Bolso database and AI processor

## Quick Start

### 1. Environment Setup

Copy the environment template:
```bash
cp .env.example .env
```

Configure your environment variables:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
AI_PROCESSOR_URL=https://saude-ai-processor-production-bebd.up.railway.app
```

### 2. Local Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the bot:
```bash
python main.py
```

### 3. Railway Deployment

Connect your repository to Railway and deploy:
```bash
railway login
railway link
railway up
```

Set environment variables in Railway dashboard or CLI:
```bash
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables set SUPABASE_URL=your_url
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_key
```

## Bot Commands

### Authentication
- `/start` - Welcome message and bot introduction
- `/login email password` - Authenticate as doctor
- `/logout` - Sign out from current session
- `/status` - Check authentication and patient status

### Patient Management
- `/patient PIN` - Search and select patient by PIN
- Send 6-digit PIN directly - Quick patient search

### Consultation Processing
- **Send voice messages** - Bot will:
  1. 🎤 **Transcribe** audio using OpenAI Whisper
  2. 📋 **Generate prontuário** using GPT-4o in SOAP format
  3. 📱 **Return both** transcript and structured medical record
- Send audio files - Support for various audio formats
- Send audio documents - Handle audio files sent as documents

### Help
- `/help` - Show all available commands and usage instructions

## Usage Workflow

1. **Login as Doctor**:
   ```
   /login doctor@example.com mypassword
   ```

2. **Select Patient**:
   ```
   /patient 123456
   ```
   Or simply send the PIN:
   ```
   123456
   ```

3. **Record Consultation**:
   - Press and hold the microphone button in Telegram
   - Record your consultation notes
   - Release to send the voice message
   - Bot will automatically transcribe and generate prontuário

## Architecture

### Services
- **AuthService**: Handles doctor authentication and patient search via Supabase
- **AIService**: Processes audio transcription and medical record generation via Railway AI processor

### Handlers
- **MessageHandlers**: Processes all Telegram messages and commands
- **Audio Processing**: Handles voice messages, audio files, and documents

### Utilities
- **Audio Utils**: Audio conversion, validation, and optimization for transcription

## Audio Processing Pipeline

1. **Download**: Receive audio from Telegram
2. **Validation**: Check audio format and duration
3. **Normalization**: Optimize volume levels
4. **Noise Reduction**: Apply filters for better transcription (if ffmpeg available)
5. **Transcription**: Send to AI processor for speech-to-text
6. **Medical Processing**: Generate structured prontuário
7. **Storage**: Save to database with patient context

## Integration with Saúde no Bolso

The bot uses the same backend infrastructure as the web application:

- **Database**: Supabase PostgreSQL with profiles, medical data, and consultations
- **Authentication**: Same doctor credentials as web app
- **AI Processing**: Railway-deployed AI processor with medical agents
- **Patient Data**: Access to complete medical history and context

### AI Processing Pipeline

1. **Audio Reception**: Telegram bot receives voice message from doctor
2. **Direct Processing**: Sends audio directly to AI processor endpoint `/api/doctor/process-direct`
3. **Transcription**: AI processor uses OpenAI Whisper to convert speech to text
4. **Prontuário Generation**: AI processor uses GPT-4o to create structured medical record
5. **Response**: Bot returns both transcript and prontuário to doctor via Telegram

**Key Difference from Web App**: The Telegram bot bypasses Supabase Storage and processes audio directly, making it more efficient for real-time chat interactions.

## Security Features

- JWT-based session management
- 24-hour session expiration
- Temporary file cleanup
- No credential storage in bot memory
- Encrypted communication with backend services

## Error Handling

The bot includes comprehensive error handling for:
- Authentication failures
- Patient not found scenarios
- Audio processing errors
- AI service unavailability
- Network connectivity issues

## Dependencies

Key Python packages:
- `python-telegram-bot==20.7` - Telegram Bot API
- `supabase==2.3.4` - Database integration
- `httpx==0.26.0` - Async HTTP client
- `pydub==0.25.1` - Audio processing
- `aiofiles==23.2.1` - Async file operations
- `loguru==0.7.2` - Structured logging

## Development

### Testing
```bash
# Test authentication
python -c "from services.auth_service import AuthService; print('Auth service loaded')"

# Test AI integration
python -c "from services.ai_service import AIService; print('AI service loaded')"
```

### Logs
The bot uses structured logging with Loguru. Check logs for:
- Authentication events
- Audio processing status
- API communication
- Error diagnostics

### Contributing
1. Follow existing code patterns
2. Add proper error handling
3. Update documentation for new features
4. Test with real Telegram bot before deployment

## Support

For issues and questions:
- Check the logs for detailed error messages
- Verify environment variables are set correctly
- Ensure AI processor service is running
- Confirm Supabase database connectivity