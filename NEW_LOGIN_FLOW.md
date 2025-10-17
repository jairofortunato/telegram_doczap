# New Multi-Step Login Flow

## Changes Made

Updated the login flow to be more conversational and concise across both Telegram and WhatsApp platforms.

## New Login Flow

### Step 1: /start or "início"
**User:** Sends `/start` (Telegram) or "início" (WhatsApp)

**Bot Response:**
```
*Bem-vindo ao ProntoDoc!*

Criar conta:
https://prontuarioautomatico.vercel.app/signup

Fazer login:
Envie seu email
```

### Step 2: Send Email
**User:** Sends email (e.g., `doctor@example.com`)

**Bot Response:**
```
🔐 Agora envie sua senha
```

### Step 3: Send Password
**User:** Sends password

**Bot Response (Success):**
```
✅ Login realizado!

Bem-vindo, Dr(a). [Nome]

🎙️ Envie um áudio da consulta
📋 Usa o *Prontuário de Consulta Rápida*

💡 Criar formato próprio:
https://prontuarioautomatico.vercel.app/doctor/formatos-anamnese
```

**Bot Response (Failure):**
```
❌ Senha incorreta

Envie /start para tentar novamente
```

## Key Features

### Multi-Step State Management
- `start_login(user_id, email)` - Stores email, waits for password
- `get_pending_login(user_id)` - Retrieves pending login state
- `clear_pending_login(user_id)` - Clears state after login attempt
- Auto-expires after 5 minutes

### Security
- Password never logged
- State cleared on logout
- Session expires after 24 hours

### Concise Messages
All messages are now shorter and more direct:
- `/status` - Shows doctor name + template + prompt to send audio
- `/help` - Simple list of commands + 4-step usage
- `/templates` - Clean list without verbose descriptions
- Error messages - Direct and actionable

## Updated Files

### 1. `services/auth_service.py`
- Added `pending_logins` dictionary
- Added `start_login()`, `get_pending_login()`, `clear_pending_login()` methods
- Auto-expiry after 5 minutes for pending logins

### 2. `main.py` (Telegram)
- Removed `/login <email> <password>` command
- Added `handle_text_input()` for multi-step flow
- Updated all messages to be concise
- `/start` now shows signup link + asks for email
- Text inputs handled as: email → password → login

### 3. `handlers/whatsapp_handler.py`
- Updated `handle_text_message()` with multi-step flow
- Removed old `handle_login_attempt()` method
- Updated all messages to match Telegram conciseness
- Same flow: email → password → login

## Commands Reference

### Available Commands
- `/start` - Start bot and show login instructions
- `/status` - View current session status
- `/templates` - List available templates
- `/template <number>` - Select a template
- `/logout` - Logout and clear session
- `/help` - Show commands
- `/cadastrar` - Show signup link
- `/debug` - System debug info (Telegram only)

### Text Input Behavior

**Not logged in:**
- Email format (contains @ and .) → Start login flow, ask for password
- Not email format → Show error, ask to use /start

**Waiting for password:**
- Any text → Attempt login with stored email
- Success → Welcome message with Prontuário de Consulta Rápida info
- Failure → Error message, suggest /start

**Logged in:**
- "templates" → Show templates list
- Other text → Remind to send audio or use /templates

## Template Message

The success login message now mentions:
- "Prontuário de Consulta Rápida" (default quick consultation format)
- Link to create custom formats on website
- Clear call-to-action to send audio

This sets expectations that:
1. Audio processing is ready immediately
2. Default format is being used
3. Custom formats can be created on website if desired

## Benefits

✅ **More natural** - Feels like a conversation, not CLI commands
✅ **Simpler** - Users don't need to remember command syntax
✅ **Secure** - Password in separate message, never logged
✅ **Clear** - Each step has explicit instructions
✅ **Consistent** - Same flow on Telegram and WhatsApp
✅ **Concise** - All messages are direct and to the point
✅ **Informative** - Login success mentions default template and link to customize

## Migration Notes

**Breaking Change:** The old `/login email password` command no longer works.

**Users must:**
1. Send `/start`
2. Send email
3. Send password

**State persistence:** Login state is in-memory and cleared on:
- Successful login
- Failed login
- 5 minute timeout
- Server restart
- Logout command
