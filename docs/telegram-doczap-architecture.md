# DocZap Multi-Platform Bot - Architecture Documentation

## Overview

The **DocZap Multi-Platform Bot** (`telegram-doczap`) is a FastAPI-based webhook service that provides medical transcription and consultation management capabilities through both **Telegram** and **WhatsApp** platforms. The system integrates with the broader **Saúde no Bolso** ecosystem to deliver AI-powered healthcare assistance.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Telegram Bot  │    │  WhatsApp API   │    │    DocZap Bot    │
│   (BotFather)   │    │ (Meta Business) │    │   (Railway)      │
└─────────┬───────┘    └─────────┬───────┘    └────────┬─────────┘
          │                      │                     │
          └──────────────────────┼─────────────────────┘
                                 │
          ┌────────────────────────────────────────────┐
          │           FastAPI Webhook Server           │
          │         (telegram-doczap service)          │
          └────────────────────┬───────────────────────┘
                               │
    ┌─────────────────────────────────────────────────────┐
    │                 Service Layer                       │
    ├─────────────────┬───────────────┬───────────────────┤
    │   Auth Service  │  AI Service   │ WhatsApp Service  │
    │   (Supabase)    │  (OpenAI)     │  (Meta Graph)     │
    └─────────────────┴───────────────┴───────────────────┘
                               │
          ┌────────────────────────────────────────────┐
          │           External Services                │
          ├─────────────────┬──────────────────────────┤
          │  AI Processor   │    Web Application       │
          │   (Railway)     │     (Vercel)            │
          └─────────────────┴──────────────────────────┘
```

### Core Components

#### 1. **FastAPI Application** (`main.py`)
- **Webhook Server**: Handles incoming messages from Telegram and WhatsApp
- **Multi-platform Support**: Single codebase serving both messaging platforms
- **Health Monitoring**: Provides `/health` endpoint for Railway deployment
- **Authentication**: Integrates with Supabase for user management

#### 2. **Service Layer**

##### **Auth Service** (`services/auth_service.py`)
- **User Authentication**: CPF/PIN based authentication for patients
- **Session Management**: Maintains user sessions across platforms
- **Supabase Integration**: Handles database operations for user data

##### **AI Service** (`services/ai_service.py`)
- **Medical Processing**: Interfaces with AI processor for medical text analysis
- **Template Management**: Fetches and manages medical consultation templates
- **Integration Layer**: Connects to external AI processor service

##### **WhatsApp Service** (`services/whatsapp_service.py`)
- **Meta Graph API**: Handles WhatsApp Business API communication
- **URL Sanitization**: Implements clean URL generation to avoid encoding issues
- **Message Types**: Supports text, audio, and interactive messages
- **Media Handling**: Downloads and processes media files from WhatsApp

#### 3. **Handler Layer**

##### **WhatsApp Handler** (`handlers/whatsapp_handler.py`)
- **Message Processing**: Routes different WhatsApp message types
- **User Flow Management**: Handles authentication and consultation flows
- **Interactive Messages**: Creates button-based user interfaces
- **Media Processing**: Handles voice messages and file uploads

#### 4. **Utility Layer**

##### **URL Utils** (`utils/url_utils.py`)
- **String Sanitization**: Removes invisible Unicode characters
- **URL Construction**: Builds clean Facebook Graph API URLs
- **Character Cleaning**: Handles zero-width spaces and control characters

## Key Features

### Multi-Platform Support
- **Telegram Integration**: Full webhook-based Telegram bot functionality
- **WhatsApp Business API**: Official Meta Business API integration
- **Unified Codebase**: Single service handles both platforms

### Medical Capabilities
- **AI-Powered Transcription**: Converts voice messages to medical text
- **Template System**: Pre-defined medical consultation templates
- **Patient Authentication**: Secure CPF/PIN based patient access
- **Consultation Management**: Creates and manages medical consultations

### Technical Features
- **Webhook Architecture**: Event-driven message processing
- **Async Processing**: Non-blocking I/O for better performance
- **URL Encoding Fixes**: Robust handling of Meta API URL requirements
- **Health Monitoring**: Built-in health checks for deployment monitoring

## Data Flow

### WhatsApp Message Processing

```
1. User sends message → WhatsApp Business API
2. Meta sends webhook → DocZap /webhook endpoint
3. Message validation and parsing
4. User authentication check
5. Route to appropriate handler
6. Process message (text/audio/interactive)
7. Call AI service if needed
8. Generate response
9. Send response via WhatsApp API
```

### Telegram Message Processing

```
1. User sends message → Telegram Bot API
2. Telegram sends webhook → DocZap /telegram/webhook
3. Message validation and parsing
4. User authentication check
5. Route to appropriate handler
6. Process message and commands
7. Call AI service if needed
8. Generate response
9. Send response via Telegram API
```

## Environment Configuration

### Required Environment Variables

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_API_VERSION=v18.0

# Webhook Verification
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# External Services
AI_PROCESSOR_URL=https://saude-ai-processor-production-bebd.up.railway.app
WEB_APP_URL=https://prontuarioautomatico.vercel.app

# Deployment
PORT=8000
```

## Deployment Architecture

### Railway Deployment Strategy

The service is deployed on Railway using **Nixpacks** instead of Docker to avoid Docker Hub authentication issues:

#### **Nixpacks Configuration** (`nixpacks.toml`)
```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "ffmpeg"]

[phases.install]
cmds = [
    "python -m pip install --upgrade pip",
    "pip install -r requirements.txt"
]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300 --timeout-graceful-shutdown 300"

[variables]
PYTHONUNBUFFERED = "1"
PORT = "8000"
```

#### **Key Deployment Features**
- **No Docker Dependency**: Uses Nixpacks to avoid Docker Hub auth issues
- **Python 3.11**: Modern Python runtime with full async support
- **FFmpeg Support**: For audio processing capabilities
- **Long Timeout Support**: Handles long-running medical processing tasks
- **Health Checks**: Built-in `/health` endpoint for monitoring

### Scalability Considerations
- **Stateless Design**: Service can be horizontally scaled
- **Async Processing**: Non-blocking I/O for better concurrency
- **External State**: Uses Supabase for persistent data storage
- **Service Isolation**: Clear separation between bot logic and AI processing

## API Endpoints

### Core Endpoints

| Endpoint | Method | Purpose | Platform |
|----------|--------|---------|----------|
| `/webhook` | POST | WhatsApp message webhooks | WhatsApp |
| `/webhook` | GET | WhatsApp webhook verification | WhatsApp |
| `/telegram/webhook` | POST | Telegram message webhooks | Telegram |
| `/health` | GET | Health check for monitoring | System |
| `/` | GET | Service status | System |

### Webhook Security
- **Signature Verification**: WhatsApp webhook signature validation
- **Token Validation**: Telegram webhook token verification
- **Environment Isolation**: Sensitive tokens stored as environment variables

## Error Handling

### WhatsApp API Error Handling
- **URL Encoding Issues**: Automatic character sanitization
- **Token Expiration**: Clear error messages for expired tokens
- **Rate Limiting**: Graceful handling of API limits
- **Message Failures**: Retry logic for failed message sends

### General Error Handling
- **Graceful Degradation**: Service continues running on partial failures
- **Logging**: Comprehensive logging with loguru
- **Health Monitoring**: Automatic health status reporting

## Security Features

### Data Protection
- **Environment Variables**: All sensitive data stored as environment variables
- **Token Security**: No hardcoded tokens or secrets
- **Input Validation**: All user inputs validated and sanitized
- **URL Sanitization**: Prevents injection attacks via malformed URLs

### API Security
- **Webhook Verification**: All incoming webhooks verified
- **HTTPS Only**: All external API calls use HTTPS
- **Access Control**: User authentication required for medical features

## Integration Points

### External Services

#### **AI Processor Service**
- **URL**: `https://saude-ai-processor-production-bebd.up.railway.app`
- **Purpose**: Medical text processing and analysis
- **Integration**: RESTful API calls for medical processing

#### **Web Application**
- **URL**: `https://prontuarioautomatico.vercel.app`
- **Purpose**: Template management and web interface
- **Integration**: Template fetching and user management

#### **Supabase Database**
- **Purpose**: User authentication and session management
- **Integration**: Row-level security for patient data protection

## Monitoring and Observability

### Logging Strategy
- **Structured Logging**: Uses loguru for consistent log formatting
- **Log Levels**: Appropriate debug, info, warning, and error levels
- **Request Tracking**: All webhook requests logged with context
- **Performance Metrics**: Response times and processing metrics

### Health Monitoring
- **Health Endpoint**: `/health` provides service status
- **Dependency Checks**: Monitors external service availability
- **Railway Integration**: Automatic restart on health check failures

## Development Workflow

### Local Development
1. **Environment Setup**: Copy `.env.example` to `.env`
2. **Virtual Environment**: Create Python virtual environment
3. **Dependencies**: Install requirements via `pip install -r requirements.txt`
4. **Local Server**: Run with `uvicorn main:app --reload`

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end webhook testing
- **Manual Testing**: Real platform testing with test accounts

### Deployment Process
1. **Code Push**: Push to connected Git repository
2. **Automatic Build**: Railway builds using Nixpacks
3. **Environment Variables**: Set in Railway dashboard
4. **Health Check**: Automatic health monitoring after deployment

## Future Enhancements

### Planned Features
- **Message Templates**: Dynamic template management
- **Multi-language Support**: Portuguese and English interfaces
- **Advanced Analytics**: User interaction analytics
- **File Processing**: Enhanced media processing capabilities

### Technical Improvements
- **Caching Layer**: Redis integration for session management
- **Queue System**: Background job processing for long tasks
- **API Rate Limiting**: Built-in rate limiting for API calls
- **Monitoring Dashboard**: Comprehensive service monitoring

## Troubleshooting

### Common Issues

#### **WhatsApp Token Expiration**
- **Symptom**: `OAuthException` errors in logs
- **Solution**: Refresh token in Meta Business Manager
- **Prevention**: Set up token refresh automation

#### **Deployment Issues**
- **Docker Hub Auth**: Use Nixpacks instead of Docker
- **Environment Variables**: Verify all required variables are set
- **Health Checks**: Monitor `/health` endpoint status

#### **Message Processing Failures**
- **URL Encoding**: Check for invisible characters in environment variables
- **API Limits**: Monitor rate limiting and implement backoff
- **Network Issues**: Implement retry logic for external API calls

---

*This documentation reflects the current state of the DocZap Multi-Platform Bot as of September 2024. For updates and changes, refer to the project's Git history and changelog.*