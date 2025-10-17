# ProntoDoc Improvements - Implementation Tasks

## Overview

This document outlines the required changes to transform the current DocZap Multi-Platform Bot into **ProntoDoc** with improved user experience, updated messaging, and streamlined audio processing workflow.

## Changes Required

### 1. **Welcome Message Redesign**

#### **Current Implementation**
The bot currently shows a generic multi-option menu after `/start`.

#### **Required Change**
**New Welcome Message:**
```
Bem-vindo ao ProntoDoc!
📋 Prontuário Automático Estruturado

Aqui você pode enviar áudios das suas consultas e receber de volta um prontuário automático no formato SOAP.

Selecione uma opção para começar:
1️⃣ Login
2️⃣ Criar Conta
```

#### **Implementation Tasks**
- [x] Update welcome message text in both Telegram and WhatsApp handlers
- [x] Simplify button options to only "Login" and "Criar Conta"
- [x] Update branding from "DocZap" to "ProntoDoc"
- [x] Ensure consistent messaging across both platforms

**Files to Modify:**
- `handlers/whatsapp_handler.py`
- `main.py` (Telegram start command handler)

### 2. **Signup Link Correction**

#### **Current Implementation**
Signup button may redirect to incorrect URL or generic signup page.

#### **Required Change**
**Target URL:** `https://prontuarioautomatico.vercel.app/signup`

#### **Implementation Tasks**
- [ ] Update "Criar Conta" button to redirect to correct signup URL
- [ ] Verify URL accessibility and functionality
- [ ] Test redirect behavior on both Telegram and WhatsApp
- [ ] Ensure URL opens in web browser correctly

**Files to Modify:**
- `handlers/whatsapp_handler.py` (interactive message buttons)
- `main.py` (Telegram inline keyboards)

### 3. **Post-Login Success Message**

#### **Current Implementation**
Generic login success message without personalization or clear next steps.

#### **Required Change**
**New Success Message:**
```
✅ Login realizado com sucesso!

Bem-vindo, Dr(a). Gabriel Meister 👋

Agora você pode:
🎙️ Enviar o áudio da sua consulta — ele será automaticamente transcrito no formato SOAP padrão.
⚙️ Se quiser criar seu próprio formato de prontuário, clique aqui: https://prontuarioautomatico.vercel.app/doctor/formatos-anamnese
📂 Você pode digitar "templates" para ver os modelos disponíveis.
```

#### **Implementation Tasks**
- [ ] Create dynamic message with user's name (Dr(a). {name})
- [ ] Add clear instructions for audio processing
- [ ] Include link to custom format creation
- [ ] Add "templates" command information
- [ ] Implement user name extraction from authentication service

**Files to Modify:**
- `services/auth_service.py` (extract user name after login)
- `handlers/whatsapp_handler.py` (post-login message)
- `main.py` (Telegram login success handler)

### 4. **Streamlined Audio Processing**

#### **Current Implementation**
Users must select a template before audio processing begins.

#### **Required Change**
**Direct SOAP Processing:**
- Immediately process any audio with SOAP padrão template
- No template selection required
- Optional "templates" command for users who want alternatives

#### **Implementation Tasks**
- [ ] Remove template selection requirement for audio messages
- [ ] Set "SOAP padrão" as default template for all audio processing
- [ ] Implement immediate audio transcription after login
- [ ] Add optional "templates" command for template browsing
- [ ] Ensure audio processing works without user template choice

**Files to Modify:**
- `handlers/whatsapp_handler.py` (`handle_audio_message` method)
- `main.py` (Telegram audio message handler)
- `services/ai_service.py` (default template logic)

## Implementation Plan

### **Phase 1: Message Updates** (Priority: High)

#### **Task 1.1: Update Welcome Message**
**Estimated Time:** 2 hours
**Dependencies:** None

**Steps:**
1. Locate current welcome/start message handlers
2. Replace message text with new ProntoDoc branding
3. Update button options (Login, Criar Conta only)
4. Test on both Telegram and WhatsApp

#### **Task 1.2: Fix Signup URL**
**Estimated Time:** 1 hour
**Dependencies:** Task 1.1

**Steps:**
1. Update "Criar Conta" button URL
2. Verify URL `https://prontuarioautomatico.vercel.app/signup`
3. Test redirect functionality
4. Ensure cross-platform compatibility

#### **Task 1.3: Update Login Success Message**
**Estimated Time:** 3 hours
**Dependencies:** Auth service integration

**Steps:**
1. Extract user name from authentication response
2. Create personalized welcome message
3. Add instructional content and links
4. Test with real user login flow

### **Phase 2: Audio Processing Simplification** (Priority: High)

#### **Task 2.1: Remove Template Selection Requirement**
**Estimated Time:** 4 hours
**Dependencies:** AI service integration

**Steps:**
1. Identify current template selection logic
2. Set "SOAP padrão" as default template
3. Modify audio processing to skip template selection
4. Update audio message handlers for immediate processing

#### **Task 2.2: Implement Optional Templates Command**
**Estimated Time:** 2 hours
**Dependencies:** Task 2.1

**Steps:**
1. Create "templates" command handler
2. Display available templates list
3. Allow template selection for future audio messages
4. Maintain user template preference in session

### **Phase 3: Testing and Validation** (Priority: Medium)

#### **Task 3.1: End-to-End Testing**
**Estimated Time:** 4 hours
**Dependencies:** All previous tasks

**Steps:**
1. Test complete user flow (welcome → login → audio processing)
2. Verify both Telegram and WhatsApp functionality
3. Test error scenarios and edge cases
4. Validate audio processing with SOAP template

#### **Task 3.2: User Acceptance Testing**
**Estimated Time:** 2 hours
**Dependencies:** Task 3.1

**Steps:**
1. Test with real user accounts
2. Verify signup flow works correctly
3. Test audio quality and processing accuracy
4. Gather feedback on user experience

## Technical Requirements

### **Code Changes Required**

#### **1. Message Text Updates**
```python
# New welcome message constant
WELCOME_MESSAGE_PRONTODOC = """
Bem-vindo ao ProntoDoc!
📋 Prontuário Automático Estruturado

Aqui você pode enviar áudios das suas consultas e receber de volta um prontuário automático no formato SOAP.

Selecione uma opção para começar:
1️⃣ Login
2️⃣ Criar Conta
"""

# New login success message template
LOGIN_SUCCESS_MESSAGE_TEMPLATE = """
✅ Login realizado com sucesso!

Bem-vindo, Dr(a). {user_name} 👋

Agora você pode:
🎙️ Enviar o áudio da sua consulta — ele será automaticamente transcrito no formato SOAP padrão.
⚙️ Se quiser criar seu próprio formato de prontuário, clique aqui: https://prontuarioautomatico.vercel.app/doctor/formatos-anamnese
📂 Você pode digitar "templates" para ver os modelos disponíveis.
"""
```

#### **2. URL Constants**
```python
# Updated URLs
SIGNUP_URL = "https://prontuarioautomatico.vercel.app/signup"
CUSTOM_FORMATS_URL = "https://prontuarioautomatico.vercel.app/doctor/formatos-anamnese"

# Default template
DEFAULT_TEMPLATE = "SOAP padrão"
```

#### **3. Audio Processing Logic**
```python
async def handle_audio_message(self, user_id: str, audio_data: dict):
    """Process audio immediately with default SOAP template"""
    if not self.is_authenticated(user_id):
        await self.request_authentication(user_id)
        return

    # Use default SOAP template - no selection required
    template = DEFAULT_TEMPLATE

    # Process audio immediately
    await self.process_audio_with_template(user_id, audio_data, template)
```

### **Dependencies and Integration**

#### **Authentication Service Updates**
- Extract user name from login response
- Store user preferences for template selection
- Maintain session state for authenticated users

#### **AI Service Integration**
- Ensure "SOAP padrão" template is always available
- Handle immediate audio processing without template selection
- Maintain template list for optional "templates" command

#### **Web Application Integration**
- Verify signup URL functionality
- Test custom formats URL accessibility
- Ensure proper redirect handling

## Quality Assurance

### **Testing Checklist**

#### **Functionality Tests**
- [ ] Welcome message displays correctly on Telegram
- [ ] Welcome message displays correctly on WhatsApp
- [ ] "Login" button works properly
- [ ] "Criar Conta" redirects to correct signup URL
- [ ] Login success message shows user name
- [ ] Audio processing works immediately after login
- [ ] "templates" command displays available templates
- [ ] Template selection affects future audio processing

#### **Cross-Platform Tests**
- [ ] All features work identically on Telegram and WhatsApp
- [ ] URLs open correctly in both platforms
- [ ] Interactive elements function properly
- [ ] Audio processing maintains consistency

#### **Error Handling Tests**
- [ ] Unauthenticated audio messages prompt for login
- [ ] Invalid audio files show appropriate error messages
- [ ] Network failures handle gracefully
- [ ] Template loading errors don't break functionality

## Documentation Updates

### **Required Documentation Changes**

#### **User-Facing Documentation**
- [ ] Update README with new ProntoDoc branding
- [ ] Create user guide for streamlined audio workflow
- [ ] Document "templates" command usage
- [ ] Update API documentation with new message formats

#### **Technical Documentation**
- [ ] Update architecture docs with new flow diagrams
- [ ] Document template selection logic changes
- [ ] Update deployment guide with new constants
- [ ] Revise troubleshooting guide for new features

## Risk Assessment

### **Potential Issues**

#### **High Risk**
- **Template Availability**: Default "SOAP padrão" template must always be available
- **Authentication Integration**: User name extraction might fail
- **URL Accessibility**: External URLs must remain accessible

#### **Medium Risk**
- **Cross-Platform Compatibility**: Features must work on both Telegram and WhatsApp
- **Audio Processing**: Immediate processing might impact performance
- **User Experience**: Changes might confuse existing users

#### **Low Risk**
- **Message Formatting**: Text formatting might vary across platforms
- **Button Layout**: Interactive elements might display differently

### **Mitigation Strategies**

#### **Template Fallback**
- Implement fallback mechanism if "SOAP padrão" is unavailable
- Cache template data locally to reduce API dependencies
- Graceful degradation if template service is down

#### **Authentication Robustness**
- Handle missing user name gracefully (use default greeting)
- Implement retry logic for authentication failures
- Maintain backwards compatibility with existing auth flow

#### **URL Monitoring**
- Implement health checks for external URLs
- Provide alternative paths if URLs are inaccessible
- Log and alert on URL failures

## Success Metrics

### **Key Performance Indicators**

#### **User Experience Metrics**
- **Signup Conversion Rate**: Percentage of users who complete signup
- **Audio Processing Success Rate**: Percentage of successful audio transcriptions
- **User Retention**: Users who return after initial audio processing
- **Error Rate**: Frequency of processing errors or failures

#### **Technical Metrics**
- **Response Time**: Average time from audio upload to transcription
- **Template Loading Time**: Speed of template retrieval and processing
- **Cross-Platform Consistency**: Feature parity between Telegram and WhatsApp
- **System Reliability**: Uptime and availability metrics

### **Acceptance Criteria**

#### **Must Have**
- [ ] All message updates implemented and tested
- [ ] Audio processing works without template selection
- [ ] Signup URL redirect functions correctly
- [ ] Cross-platform compatibility maintained

#### **Should Have**
- [ ] "templates" command provides easy template access
- [ ] User name personalization works consistently
- [ ] Error handling provides clear user feedback
- [ ] Performance maintains current standards

#### **Nice to Have**
- [ ] Enhanced user onboarding experience
- [ ] Template preference persistence
- [ ] Advanced audio processing options
- [ ] Usage analytics and monitoring

---

**Total Estimated Implementation Time:** 18 hours
**Recommended Sprint Duration:** 1-2 weeks
**Team Members Required:** 1-2 developers
**Priority Level:** High (impacts core user experience)

*This task document should be reviewed and approved before implementation begins. Each task should be tracked in the project management system with appropriate time estimates and dependencies.*