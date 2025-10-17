# WhatsApp Integration - Technical Guide

## Overview

This document details the WhatsApp Business API integration in the DocZap Multi-Platform Bot, including the critical URL encoding fixes that resolve the "Invalid non-printable ASCII character in URL" errors that were preventing successful message exchanges.

## WhatsApp Business API Integration

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│     User        │    │  WhatsApp       │    │   DocZap Bot     │
│   (WhatsApp)    │    │ Business API    │    │   (Railway)      │
└─────────┬───────┘    └─────────┬───────┘    └────────┬─────────┘
          │                      │                     │
          │ 1. Send Message      │                     │
          ├─────────────────────→│                     │
          │                      │ 2. Webhook POST     │
          │                      ├────────────────────→│
          │                      │                     │ 3. Process
          │                      │                     │ Message
          │                      │ 4. API Call         │
          │                      │←────────────────────┤
          │ 5. Receive Response  │                     │
          │←─────────────────────┤                     │
```

### Key Components

#### 1. **WhatsApp Service** (`services/whatsapp_service.py`)

The WhatsApp service handles all interactions with the Meta Graph API:

```python
class WhatsAppService:
    def __init__(self):
        # Clean environment variables to remove invisible characters
        self.access_token = clean_string(os.getenv('WHATSAPP_ACCESS_TOKEN', ''))
        self.phone_number_id = clean_string(os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''))
        self.api_version = clean_string(os.getenv('WHATSAPP_API_VERSION', 'v18.0'))
```

**Key Features:**
- **Async HTTP Client**: Uses `httpx.AsyncClient` for non-blocking API calls
- **URL Sanitization**: Automatically cleans URLs before API calls
- **Error Handling**: Comprehensive error handling with detailed logging
- **Media Support**: Handles text, audio, and interactive messages

#### 2. **WhatsApp Handler** (`handlers/whatsapp_handler.py`)

The handler processes incoming WhatsApp messages:

```python
class WhatsAppHandler:
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming WhatsApp message"""
        message_id = message.get('id')
        from_number = message.get('from')

        # Mark message as read (with clean URLs)
        await self.whatsapp.mark_as_read(message_id)

        # Process different message types
        if 'text' in message:
            await self.handle_text_message(user_id, message['text']['body'])
        elif 'audio' in message or 'voice' in message:
            await self.handle_audio_message(user_id, message.get('audio', message.get('voice')))
```

## Critical URL Encoding Fix

### The Problem

The integration was failing with this error:
```
Error: Invalid non-printable ASCII character in URL
```

This occurred because environment variables (especially when copied from Meta Developer Console) contained invisible Unicode characters like:
- Zero-width spaces (U+200B)
- Byte Order Mark (U+FEFF)
- Word joiners (U+2060)
- Control characters

### The Solution: URL Utils Module

#### **URL Sanitization** (`utils/url_utils.py`)

```python
def clean_string(s: str) -> str:
    """Clean string by removing non-printable ASCII characters and zero-width spaces"""
    if not s:
        return ""

    # Remove zero-width spaces and other problematic Unicode characters
    s = s.replace("\u200b", "")  # Zero-width space
    s = s.replace("\ufeff", "")  # Byte order mark
    s = s.replace("\u2060", "")  # Word joiner

    # Remove all control characters except newline and tab
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", s)

    return s.strip()

def build_graph_api_url(api_version: str, phone_number_id: str, endpoint: str = "messages") -> str:
    """Build clean Facebook Graph API URL"""
    base_url = "https://graph.facebook.com/"

    # Clean all components
    api_version = clean_string(api_version)
    phone_number_id = clean_string(phone_number_id)
    endpoint = clean_string(endpoint).lstrip("/")

    # Ensure api_version starts with 'v'
    if not api_version.startswith('v'):
        api_version = f"v{api_version}"

    # Build URL step by step
    version_url = urljoin(base_url, f"{api_version}/")
    final_url = urljoin(version_url, f"{phone_number_id}/{endpoint}")

    return final_url
```

#### **Implementation in WhatsApp Service**

The service now uses these utilities in all API calls:

```python
async def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
    try:
        # Build clean URL
        url = build_graph_api_url(self.api_version, self.phone_number_id, "messages")
        logger.debug(f"WhatsApp send_text URL: {repr(url)}")

        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone_number(to),
            "type": "text",
            "text": {"body": text}
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = await self.client.post(url, json=payload, headers=headers)
```

### Before vs After

#### **Before (Broken)**
```python
# Environment variable with invisible characters
WHATSAPP_PHONE_NUMBER_ID="775098139028859\u200b"  # Zero-width space at end

# Direct URL construction
url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
# Results in: "https://graph.facebook.com/v18.0/775098139028859​/messages"
# The invisible character breaks HTTP requests
```

#### **After (Fixed)**
```python
# Clean environment variables on initialization
self.phone_number_id = clean_string(os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''))

# Clean URL construction
url = build_graph_api_url(self.api_version, self.phone_number_id, "messages")
# Results in: "https://graph.facebook.com/v18.0/775098139028859/messages"
# Clean URL that works properly
```

## WhatsApp API Endpoints

### Supported Operations

#### 1. **Send Text Messages**
```python
await whatsapp_service.send_text_message(
    to="554899263038",
    text="Olá! Como posso ajudar?"
)
```

#### 2. **Send Interactive Messages**
```python
buttons = [
    {"id": "login", "title": "🔐 Login"},
    {"id": "help", "title": "❓ Ajuda"},
    {"id": "status", "title": "📊 Status"}
]

await whatsapp_service.send_interactive_message(
    to="554899263038",
    header_text="DocZap",
    body_text="Escolha uma opção:",
    footer_text="Powered by Saúde no Bolso",
    buttons=buttons
)
```

#### 3. **Mark Messages as Read**
```python
await whatsapp_service.mark_as_read(message_id)
```

#### 4. **Download Media**
```python
media_content = await whatsapp_service.download_media(media_id)
```

## Webhook Configuration

### Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook` | GET | Webhook verification |
| `/webhook` | POST | Message processing |

### Webhook Verification

```python
@app.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    """Verify WhatsApp webhook subscription"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Forbidden")
```

### Message Processing

```python
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    data = await request.json()
    logger.info(f"📨 Received WhatsApp webhook POST: {data}")

    if data.get('object') == 'whatsapp_business_account':
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    await process_whatsapp_message_change(change.get('value', {}))

    return JSONResponse({"status": "ok"})
```

## Message Types Support

### 1. **Text Messages**
```json
{
  "from": "554899263038",
  "id": "message_id",
  "timestamp": "1758757953",
  "text": {
    "body": "Hello, DocZap!"
  },
  "type": "text"
}
```

### 2. **Audio Messages**
```json
{
  "from": "554899263038",
  "id": "message_id",
  "timestamp": "1758757953",
  "audio": {
    "id": "audio_id",
    "mime_type": "audio/ogg"
  },
  "type": "audio"
}
```

### 3. **Interactive Responses**
```json
{
  "from": "554899263038",
  "id": "message_id",
  "timestamp": "1758757953",
  "interactive": {
    "type": "button_reply",
    "button_reply": {
      "id": "login",
      "title": "🔐 Login"
    }
  },
  "type": "interactive"
}
```

## Error Handling

### Common Issues and Solutions

#### 1. **Token Expiration**
```
Error: Session has expired on Tuesday, 23-Sep-25 10:00:00 PDT
```
**Solution**: Refresh access token in Meta Business Manager

#### 2. **URL Encoding Errors**
```
Error: Invalid non-printable ASCII character in URL
```
**Solution**: Implemented automatic URL sanitization (already fixed)

#### 3. **Rate Limiting**
```
Error: Rate limit exceeded
```
**Solution**: Implement exponential backoff and retry logic

### Error Logging

All errors are logged with context for debugging:

```python
logger.error(f"❌ Failed to send WhatsApp message: {result}")
logger.debug(f"WhatsApp send_text URL: {repr(url)}")  # Shows exact URL bytes
```

## Security Considerations

### 1. **Webhook Signature Verification**

```python
def verify_whatsapp_signature(body: bytes, signature: str) -> bool:
    """Verify WhatsApp webhook signature"""
    app_secret = os.getenv('WHATSAPP_APP_SECRET', '')

    expected_signature = 'sha256=' + hmac.new(
        app_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
```

### 2. **Environment Variable Security**
- All sensitive tokens stored as environment variables
- Automatic cleaning of environment variables on startup
- No hardcoded tokens in source code

### 3. **Input Validation**
- All user inputs validated and sanitized
- Phone numbers cleaned before API calls
- Message IDs sanitized before processing

## Performance Optimizations

### 1. **Async Processing**
- All HTTP calls use async/await pattern
- Non-blocking I/O for better concurrency
- Proper connection pooling with httpx

### 2. **URL Caching**
- URL components cleaned once on initialization
- Reusable URL building functions
- Minimal string processing overhead

### 3. **Error Recovery**
- Graceful degradation on API failures
- Retry logic for transient errors
- Comprehensive error logging for debugging

## Testing

### Manual Testing Checklist

1. **Message Reception**
   - [ ] Text messages processed correctly
   - [ ] Audio messages downloaded and processed
   - [ ] Interactive button responses handled

2. **Message Sending**
   - [ ] Text responses sent successfully
   - [ ] Interactive messages display correctly
   - [ ] Media messages sent properly

3. **Error Handling**
   - [ ] Invalid messages handled gracefully
   - [ ] API errors logged appropriately
   - [ ] Service continues running after errors

### URL Sanitization Testing

```python
def test_url_sanitization():
    # Test with problematic characters
    dirty_phone_id = "775098139028859\u200b"  # Zero-width space
    clean_url = build_graph_api_url("v18.0", dirty_phone_id, "messages")

    # Should produce clean URL
    expected = "https://graph.facebook.com/v18.0/775098139028859/messages"
    assert clean_url == expected

    # Check for problematic byte sequences
    url_bytes = clean_url.encode('utf-8')
    problematic_sequences = [
        b'\xe2\x80\x8b',  # zero-width space
        b'\xef\xbb\xbf',  # BOM
        b'\xe2\x81\xa0',  # word joiner
    ]

    assert not any(seq in url_bytes for seq in problematic_sequences)
```

## Monitoring and Observability

### Log Examples

#### Successful Message Processing
```
2025-09-24 23:52:34.381 | INFO | main:whatsapp_webhook:803 - 📱 Real message from phone_number_id: 775098139028859
2025-09-24 23:52:34.381 | DEBUG | services.whatsapp_service:mark_as_read:168 - WhatsApp mark_as_read URL: 'https://graph.facebook.com/v23.0/775098139028859/messages'
2025-09-24 23:52:34.646 | INFO | handlers.whatsapp_handler:handle_message:30 - 📱 Processing WhatsApp message from 554899263038
```

#### URL Debugging
```python
# Debug logging shows exact URL representation
logger.debug(f"WhatsApp send_text URL: {repr(url)}")
# Output: WhatsApp send_text URL: 'https://graph.facebook.com/v18.0/775098139028859/messages'
```

### Health Monitoring

The service includes health checks for WhatsApp connectivity:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "whatsapp_enabled": whatsapp_service.enabled,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Future Enhancements

### Planned Improvements

1. **Template Messages**
   - Support for WhatsApp message templates
   - Dynamic template parameter injection
   - Template approval workflow integration

2. **Media Processing**
   - Enhanced audio processing for voice messages
   - Image recognition for medical documents
   - File upload and storage integration

3. **Advanced Features**
   - WhatsApp Business Profile integration
   - Catalog and product messaging
   - Location sharing capabilities

4. **Performance**
   - Message queue for high-volume processing
   - Redis caching for session management
   - Rate limiting and throttling

---

*This guide reflects the current WhatsApp integration as of September 2024, including all URL encoding fixes and error handling improvements.*