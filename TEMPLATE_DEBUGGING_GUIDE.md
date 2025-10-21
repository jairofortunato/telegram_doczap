# Template Debugging Guide - WhatsApp Bot

## Issue
WhatsApp bot shows only 1 template ("Consulta Geral") while the web app shows 3 templates for the same doctor.

## Root Cause Analysis
The issue could be one of three things:
1. **Authentication not working** - Session token not being passed correctly
2. **Database issue** - Templates not linked to doctor's profile_id
3. **API filtering issue** - Web API not recognizing the authenticated doctor

## Debugging Logs Added

I've added comprehensive logging throughout the system to help diagnose the issue.

### 1. WhatsApp Handler Logs (`handlers/whatsapp_handler.py`)

When a user types `templates`, you'll now see:
```
📋 [TEMPLATES] Fetching templates for doctor:
   - User ID: <phone_number>
   - Profile ID: <doctor_profile_id>
   - Email: <doctor_email>
   - Has session_token: True/False
   - Token length: <chars>

📋 [TEMPLATES] Received X templates from API
   1. Template Name (Specialty)
      - is_public: true/false
      - is_default: true/false
      - created_by: <profile_id>
```

### 2. AI Service Logs (`services/ai_service.py`)

When fetching templates from the web API:
```
📋 Fetching consultation templates from web app...
   - Web App URL: https://prontuarioautomatico.vercel.app
   - Doctor Profile ID: <profile_id>

🔐 Using authentication token for templates request
   - Token (first 20 chars): eyJhbGciOiJIUzI1NiIs...
   - Token (last 20 chars): ...cCI6IkpXVCJ9

📡 Making GET request to: https://prontuarioautomatico.vercel.app/api/doctor/consultation-templates
📡 Response status: 200
📡 Response JSON: success=true, count=X

✅ Found X templates from web app
   - Public templates: X
   - Default templates: X
   - Doctor's own templates: X

   1. Template Name - created_by: <id>, public: true, default: false
```

### 3. Web API Logs (`web-saude-no-bolso/src/app/api/doctor/consultation-templates/route.ts`)

In your Vercel deployment logs:
```
🔍 [GET-TEMPLATES] Checking authentication...
🔍 [GET-TEMPLATES] Auth check result: {
  hasUser: true,
  userId: <user_id>,
  userEmail: <email>,
  authError: null
}

🔍 [GET-TEMPLATES] Profile check result: {
  hasProfile: true,
  profileId: <profile_id>,
  role: 'doctor',
  profileError: null
}

👨‍⚕️ [GET-TEMPLATES] Authenticated doctor: <profile_id>

📋 [GET-TEMPLATES] Fetching consultation templates...
📋 [GET-TEMPLATES] Doctor Profile ID for filtering: <profile_id>
📋 [GET-TEMPLATES] Applying authenticated filter: is_public.eq.true,is_default.eq.true,created_by.eq.<profile_id>

✅ [GET-TEMPLATES] Database query completed:
  - Total templates returned: X
  1. "Template Name" - created_by: <id>, is_public: true, is_default: false
```

## How to Debug

### Step 1: Deploy Updated Code

1. **Deploy WhatsApp bot** (telegram-doczap):
   ```bash
   cd telegram-doczap
   railway up
   ```

2. **Deploy web app** (if you made changes):
   ```bash
   cd web-saude-no-bolso
   # Deploy to Vercel
   vercel --prod
   ```

### Step 2: Test in WhatsApp

1. **Login** to WhatsApp bot (if not already logged in):
   ```
   <your_email@example.com>
   <your_password>
   ```

2. **Request templates**:
   ```
   templates
   ```

### Step 3: Check Logs

**WhatsApp Bot Logs (Railway):**
```bash
railway logs --tail
```

Look for the `[TEMPLATES]` logs to see:
- Is session_token present?
- How many templates were returned from API?
- Which templates were returned?

**Web API Logs (Vercel):**
1. Go to Vercel Dashboard
2. Navigate to your project
3. Click "Deployments" → Latest deployment → "Functions" → Find the template API logs
4. Look for `[GET-TEMPLATES]` logs

### Step 4: Identify the Issue

Based on the logs, you'll see one of these scenarios:

#### Scenario A: Authentication Not Working
```
ℹ️ No authentication token, fetching public templates only
```
**Solution:** The session_token is not being stored or passed. Check:
- Does the login flow save `session_token` in `auth_service.py`?
- Is the session still active (not expired)?

#### Scenario B: Templates Not Linked to Doctor
```
✅ Found 1 templates from web app
   - Doctor's own templates: 0
```
**Solution:** The templates in the database don't have the correct `created_by` field.

Check database:
```sql
SELECT id, name, specialty, created_by, is_public, is_default
FROM consultation_templates
WHERE is_deleted = false
ORDER BY name;
```

Fix templates:
```sql
-- Update templates to link to your doctor profile
UPDATE consultation_templates
SET created_by = '<your_doctor_profile_id>'
WHERE name IN ('SOAP + Físico', 'SOAP c Exame Físico');
```

#### Scenario C: API Not Recognizing Doctor
```
🔍 [GET-TEMPLATES] Auth check result: { hasUser: false }
```
**Solution:** The JWT token is not being recognized by the web API.

Check:
- Is the token valid?
- Is it being sent in the Authorization header correctly?
- Check Supabase auth settings

## Expected Working Flow

When everything works correctly, you should see:

1. **WhatsApp logs:**
   ```
   📋 [TEMPLATES] Has session_token: True
   📋 [TEMPLATES] Received 3 templates from API
      - Doctor's own templates: 2
   ```

2. **Web API logs:**
   ```
   👨‍⚕️ [GET-TEMPLATES] Authenticated doctor: <your_profile_id>
   ✅ [GET-TEMPLATES] Total templates returned: 3
   ```

3. **WhatsApp message:**
   ```
   📋 Modelos:

   1. Consulta Geral (SOAP) - Clínica Geral
   2. SOAP + Físico - Geral
   3. SOAP c Exame Físico - Geral

   💡 Envie: template 1
   ```

## Quick Database Check

To see what templates exist and who owns them:

```sql
-- Check all templates
SELECT
    t.id,
    t.name,
    t.specialty,
    t.is_public,
    t.is_default,
    t.created_by,
    p.full_name as creator_name,
    p.email as creator_email
FROM consultation_templates t
LEFT JOIN profiles p ON p.profile_id = t.created_by
WHERE t.is_deleted = false
ORDER BY t.is_default DESC, t.name ASC;
```

## Next Steps

1. ✅ Deploy the updated code with logging
2. ⏳ Test in WhatsApp and check logs
3. ⏳ Identify which scenario you're in (A, B, or C)
4. ⏳ Apply the appropriate fix

Let me know what you find in the logs and I'll help you fix it!
