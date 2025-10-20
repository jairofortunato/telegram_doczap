#!/usr/bin/env python3
"""
ProntoDoc - Multi-Platform Bot for Medical Transcription
FastAPI webhook-based implementation for Telegram and WhatsApp
Railway deployment ready
"""

import os
import hmac
import hashlib
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Dict, Any

from services.auth_service import AuthService
from services.ai_service import AIService
from services.whatsapp_service import WhatsAppService
from services.subscription_service import SubscriptionService
from services.image_service import ImageProcessingService
from handlers.whatsapp_handler import WhatsAppHandler
from utils.telegram_utils import send_telegram_message, download_telegram_file, get_file_info, send_error_message
from utils.processing_state import ProcessingStateManager

# Load environment variables
load_dotenv()

app = FastAPI(title="ProntoDoc Multi-Platform Bot", version="1.0.0")

# Initialize services
auth_service = AuthService()
ai_service = AIService()
whatsapp_service = WhatsAppService()
subscription_service = SubscriptionService()
image_service = ImageProcessingService()  # New image processing service

# Initialize processing state manager to prevent duplicate processing
processing_state = ProcessingStateManager(cleanup_interval=300)  # Keep state for 5 minutes

# Initialize WhatsApp handler with all services
whatsapp_handler = WhatsAppHandler(
    whatsapp_service,
    auth_service,
    ai_service,
    subscription_service,
    processing_state,
    image_service  # Add image service
)

# Bot configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

logger.info("🤖 ProntoDoc multi-platform bot initialized successfully")
logger.info(f"📱 Telegram: Enabled")
logger.info(f"💬 WhatsApp: {'Enabled' if whatsapp_service.enabled else 'Disabled'}")
logger.info(f"📸 Image Processing: Enabled (OpenAI Vision)")

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming Telegram webhook updates"""
    try:
        data = await request.json()
        logger.debug(f"Received webhook data: {data}")

        message = data.get("message", {})
        if not message:
            return JSONResponse({"status": "no_message"})

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]

        # Handle /start command
        if message.get("text") == "/start":
            await handle_start_command(chat_id, user_id)
            return JSONResponse({"status": "start_sent"})


        # Handle /logout command
        if message.get("text") == "/logout":
            await handle_logout_command(chat_id, user_id)
            return JSONResponse({"status": "logout_processed"})

        # Handle /help command
        if message.get("text") == "/help":
            await handle_help_command(chat_id)
            return JSONResponse({"status": "help_sent"})

        # Handle /status command
        if message.get("text") == "/status":
            await handle_status_command(chat_id, user_id)
            return JSONResponse({"status": "status_sent"})

        # Handle /templates command
        if message.get("text") == "/templates":
            await handle_templates_command(chat_id, user_id)
            return JSONResponse({"status": "templates_sent"})

        # Handle /template command (with template selection)
        if message.get("text", "").startswith("/template"):
            await handle_template_command(chat_id, user_id, message.get("text", ""))
            return JSONResponse({"status": "template_processed"})

        # Handle /cadastrar command
        if message.get("text") == "/cadastrar":
            await handle_cadastrar_command(chat_id, user_id)
            return JSONResponse({"status": "cadastrar_sent"})

        # Handle /debug command (for troubleshooting)
        if message.get("text") == "/debug":
            await handle_debug_command(chat_id, user_id)
            return JSONResponse({"status": "debug_sent"})

        # Check for voice/audio content
        file_info = None
        if "voice" in message:
            file_info = message["voice"]
        elif "audio" in message:
            file_info = message["audio"]
        elif "document" in message and message["document"].get("mime_type", "").startswith("audio"):
            file_info = message["document"]

        if file_info:
            file_id = file_info["file_id"]

            # Check if this audio is already being processed or was recently completed
            if processing_state.is_processing(file_id):
                logger.warning(f"⚠️ Audio {file_id} is already being processed - ignoring duplicate request")
                return JSONResponse({"status": "already_processing"})

            if processing_state.is_completed(file_id):
                logger.warning(f"⚠️ Audio {file_id} was already processed recently - ignoring duplicate request")
                return JSONResponse({"status": "already_completed"})

            # Acknowledge receipt
            send_telegram_message(BOT_TOKEN, chat_id, "✅ Áudio recebido. Processando...")

            # Process in background
            background_tasks.add_task(process_voice_message, chat_id, user_id, file_id)
            return JSONResponse({"status": "processing"})

        # Handle text messages (email/password flow or templates)
        if "text" in message and not message["text"].startswith("/"):
            await handle_text_input(chat_id, user_id, message["text"].strip())
            return JSONResponse({"status": "text_processed"})

        return JSONResponse({"status": "message_handled"})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        logger.error(f"Webhook traceback: {traceback.format_exc()}")

        # Try to extract chat_id for error reporting if possible
        try:
            error_chat_id = None
            if hasattr(e, '__dict__') and 'chat_id' in str(e):
                # Try to extract chat_id from the error context
                pass
            elif 'data' in locals():
                error_chat_id = data.get("message", {}).get("chat", {}).get("id")

            if error_chat_id:
                send_error_message(BOT_TOKEN, error_chat_id,
                    error_type="system",
                    error_message=f"Erro no webhook do Telegram: {str(e)}",
                    error_code="WEBHOOK_ERROR",
                    details={
                        "exception_type": type(e).__name__,
                        "webhook_method": "POST /telegram/webhook"
                    },
                    suggestions=[
                        "Tente enviar a mensagem novamente",
                        "Verifique se o bot está funcionando com /start",
                        "Aguarde alguns minutos e tente novamente"
                    ])
        except:
            # If we can't send error to chat, just log it
            logger.error("Could not send webhook error to chat")

        return JSONResponse({"status": "error", "message": str(e)})

async def handle_start_command(chat_id: int, user_id: int):
    """Handle /start command"""
    # Check if already logged in
    session = auth_service.get_doctor_session(user_id)
    if session:
        send_telegram_message(BOT_TOKEN, chat_id,
            f"✅ Já logado como Doctor {session['full_name']}\n\n"
            "🎙️ Envie um áudio para transcrever.")
        return

    welcome_msg = """*Bem-vindo ao ProntoDoc!*

**Criar conta:**
https://prontuarioautomatico.vercel.app/signup

**Fazer login:**
Envie seu email"""

    send_telegram_message(BOT_TOKEN, chat_id, welcome_msg)
    logger.info(f"👋 User {user_id} started bot")

async def handle_text_input(chat_id: int, user_id: int, text: str):
    """Handle text input - email/password flow or templates"""
    try:
        # Check if user is waiting to send password
        pending_login = auth_service.get_pending_login(user_id)

        if pending_login:
            # User is sending password
            email = pending_login["email"]
            password = text

            # Authenticate
            result = await auth_service.authenticate_doctor(user_id, email, password)

            # Clear pending login
            auth_service.clear_pending_login(user_id)

            if result.get("success"):
                doctor_name = result["doctor"]["full_name"]
                send_telegram_message(BOT_TOKEN, chat_id,
                    f"✅ Login realizado!\n\n"
                    f"Bem-vindo, Doctor {doctor_name}\n\n"
                    "🎙️ Envie um áudio da consulta\n"
                    "📋 Usa o *Prontuário de Consulta Rápida*\n\n"
                    "💡 Criar formato próprio:\n"
                    "https://prontuarioautomatico.vercel.app/doctor/formatos-anamnese")
                logger.info(f"✅ Login successful for {email}")
            else:
                send_telegram_message(BOT_TOKEN, chat_id,
                    "❌ Senha incorreta\n\nEnvie /start para tentar novamente")
                logger.info(f"❌ Login failed for {email}")

        else:
            # Check if text is "templates"
            if text.lower() == "templates":
                await handle_templates_command(chat_id, user_id)
                return

            # Check if authenticated
            session = auth_service.get_doctor_session(user_id)
            if session:
                send_telegram_message(BOT_TOKEN, chat_id,
                    "🎙️ Envie um áudio para transcrever\n"
                    "📋 Use /templates para ver modelos")
                return

            # Treat as email (start login flow)
            if "@" in text and "." in text:
                auth_service.start_login(user_id, text)
                send_telegram_message(BOT_TOKEN, chat_id, "🔐 Agora envie sua senha")
                logger.info(f"🔐 Login flow started for {text}")
            else:
                send_telegram_message(BOT_TOKEN, chat_id,
                    "❌ Formato inválido\n\n"
                    "Envie /start para começar")

    except Exception as e:
        logger.error(f"Text input error: {e}")
        send_telegram_message(BOT_TOKEN, chat_id,
            "❌ Erro no login\n\nEnvie /start para tentar novamente")

async def handle_logout_command(chat_id: int, user_id: int):
    """Handle /logout command"""
    auth_service.logout(user_id)
    auth_service.clear_pending_login(user_id)
    send_telegram_message(BOT_TOKEN, chat_id, "✅ Logout realizado")
    logger.info(f"🚪 User {user_id} logged out")

async def handle_help_command(chat_id: int):
    """Handle /help command"""
    help_msg = """*Comandos:*

/start - Iniciar
/status - Ver status
/templates - Ver modelos
/logout - Sair
/help - Ajuda

*Como usar:*
1. Envie seu email
2. Envie sua senha
3. Envie áudio da consulta
4. Receba transcrição + prontuário"""

    send_telegram_message(BOT_TOKEN, chat_id, help_msg)

async def handle_status_command(chat_id: int, user_id: int):
    """Handle /status command"""
    session = auth_service.get_doctor_session(user_id)

    if session:
        doctor_name = session.get("full_name", "N/A")
        selected_template = auth_service.get_selected_template(user_id)

        if selected_template:
            template_name = selected_template.get("name", "N/A")
            template_info = f"📋 {template_name}"
        else:
            template_info = "📋 Prontuário de Consulta Rápida"

        status_msg = f"""✅ Doctor {doctor_name}
{template_info}

🎙️ Envie áudio para transcrever"""
    else:
        status_msg = """❌ Não logado

Envie /start para começar"""

    send_telegram_message(BOT_TOKEN, chat_id, status_msg)

async def handle_templates_command(chat_id: int, user_id: int):
    """Handle /templates command - show available templates"""
    try:
        session = auth_service.get_doctor_session(user_id)
        if not session:
            send_telegram_message(BOT_TOKEN, chat_id, "❌ Faça login primeiro")
            return

        result = await ai_service.get_templates(session)

        if result.get("success"):
            templates = result.get("templates", [])

            if not templates:
                send_telegram_message(BOT_TOKEN, chat_id, "❌ Nenhum modelo encontrado")
                return

            templates_msg = "📋 *Modelos:*\n\n"

            for i, template in enumerate(templates, 1):
                name = template.get("name", "N/A")
                specialty = template.get("specialty", "N/A")
                templates_msg += f"{i}. {name} - {specialty}\n"

            templates_msg += f"\n💡 Use `/template <número>`"

            # Store templates in session
            if user_id in auth_service.active_sessions:
                auth_service.active_sessions[user_id]["available_templates"] = templates

            send_telegram_message(BOT_TOKEN, chat_id, templates_msg)

        else:
            send_telegram_message(BOT_TOKEN, chat_id, "❌ Erro ao buscar modelos")

    except Exception as e:
        logger.error(f"Templates error: {e}")
        send_telegram_message(BOT_TOKEN, chat_id, "❌ Erro ao buscar modelos")

async def handle_template_command(chat_id: int, user_id: int, text: str):
    """Handle /template command - select a specific template"""
    try:
        session = auth_service.get_doctor_session(user_id)
        if not session:
            send_telegram_message(BOT_TOKEN, chat_id, "❌ Faça login primeiro")
            return

        parts = text.split()
        if len(parts) != 2:
            send_telegram_message(BOT_TOKEN, chat_id, "❌ Use: `/template <número>`")
            return

        try:
            template_index = int(parts[1]) - 1
        except ValueError:
            send_telegram_message(BOT_TOKEN, chat_id, "❌ Número inválido")
            return

        available_templates = session.get("available_templates", [])

        if not available_templates:
            send_telegram_message(BOT_TOKEN, chat_id, "❌ Use `/templates` primeiro")
            return

        if template_index < 0 or template_index >= len(available_templates):
            send_telegram_message(BOT_TOKEN, chat_id,
                f"❌ Escolha entre 1 e {len(available_templates)}")
            return

        selected_template = available_templates[template_index]
        auth_service.set_selected_template(user_id, selected_template)

        template_name = selected_template.get("name", "N/A")

        send_telegram_message(BOT_TOKEN, chat_id,
            f"✅ Modelo selecionado: {template_name}\n\n"
            "🎙️ Envie um áudio da consulta")
        logger.info(f"✅ Template '{template_name}' selected for user {user_id}")

    except Exception as e:
        logger.error(f"Template selection error: {e}")
        send_telegram_message(BOT_TOKEN, chat_id, "❌ Erro ao selecionar modelo")

async def handle_cadastrar_command(chat_id: int, user_id: int):
    """Handle /cadastrar command - provide signup link"""
    cadastrar_msg = """*Criar conta:*

https://prontuarioautomatico.vercel.app/signup

Após criar, envie /start para fazer login"""

    send_telegram_message(BOT_TOKEN, chat_id, cadastrar_msg)

async def handle_debug_command(chat_id: int, user_id: int):
    """Handle /debug command - show system status for troubleshooting"""
    try:
        session = auth_service.get_doctor_session(user_id)
        selected_template = auth_service.get_selected_template(user_id)

        debug_msg = "🔧 *Informações de Debug - ProntoDoc*\n\n"

        # Authentication Status
        debug_msg += "🔐 *Autenticação:*\n"
        if session:
            debug_msg += f"✅ Logado como: {session.get('full_name', 'N/A')}\n"
            debug_msg += f"📧 Email: {session.get('email', 'N/A')}\n"
            debug_msg += f"🆔 Profile ID: `{session.get('profile_id', 'N/A')}`\n"
            debug_msg += f"⏰ Login em: {session.get('authenticated_at', 'N/A')}\n"
        else:
            debug_msg += "❌ Não autenticado\n"

        # Template Status
        debug_msg += "\n📋 *Template:*\n"
        if selected_template:
            debug_msg += f"✅ Selecionado: {selected_template.get('name', 'N/A')}\n"
            debug_msg += f"📍 Especialidade: {selected_template.get('specialty', 'N/A')}\n"
            debug_msg += f"🆔 Template ID: `{selected_template.get('id', 'N/A')}`\n"
        else:
            debug_msg += "❌ Nenhum template selecionado\n"

        # System Status
        debug_msg += "\n🤖 *Sistema:*\n"
        debug_msg += f"🌐 AI Processor: `{ai_service.ai_processor_url}`\n"
        debug_msg += f"📱 Telegram User ID: `{user_id}`\n"
        debug_msg += f"💬 Chat ID: `{chat_id}`\n"

        # Connection Tests
        debug_msg += "\n🔍 *Testes de Conexão:*\n"
        try:
            # Test AI service connection
            test_result = await ai_service.get_templates(session) if session else {"success": False, "error": "Not authenticated"}
            if test_result.get("success"):
                debug_msg += "✅ AI Processor: Conectado\n"
            else:
                debug_msg += f"❌ AI Processor: {test_result.get('error', 'Erro na conexão')}\n"
        except Exception as e:
            debug_msg += f"❌ AI Processor: Erro - {str(e)}\n"

        # Available Templates Count
        if session:
            available_templates = session.get("available_templates", [])
            debug_msg += f"📊 Templates carregados: {len(available_templates)}\n"

        debug_msg += "\n💡 *Comandos úteis:*\n"
        debug_msg += "• `/status` - Status da sessão\n"
        debug_msg += "• `/templates` - Recarregar templates\n"
        debug_msg += "• `/logout` e `/login` - Reiniciar sessão\n"

        send_telegram_message(BOT_TOKEN, chat_id, debug_msg)
        logger.info(f"🔧 Debug info sent to user {user_id}")

    except Exception as e:
        logger.error(f"Debug command error: {e}")
        send_error_message(BOT_TOKEN, chat_id,
            error_type="system",
            error_message=f"Erro ao gerar informações de debug: {str(e)}",
            error_code="DEBUG_ERROR",
            details={"exception_type": type(e).__name__},
            suggestions=["Tente usar /status para informações básicas"])

async def process_voice_message(chat_id: int, user_id: int, file_id: str):
    """Process voice/audio message in background"""
    # Mark as processing - prevent duplicate processing
    if not processing_state.start_processing(file_id):
        logger.warning(f"⚠️ Audio {file_id} is already being processed or completed - skipping")
        return

    processing_success = False
    try:
        # Check if user is authenticated
        session = auth_service.get_doctor_session(user_id)
        if not session:
            send_telegram_message(BOT_TOKEN, chat_id,
                "❌ Você precisa fazer login primeiro. Use `/login <email> <password>`")
            processing_state.finish_processing(file_id, success=False)
            return

        # ===== SUBSCRIPTION CHECK DISABLED - Allow all users to record freely =====
        # if subscription_service:
        #     limit_check = await subscription_service.check_consultation_limit(str(user_id), session)
        #
        #     if not limit_check.get("can_create", False):
        #         # FREE TIER LIMIT EXCEEDED - Block and show payment link
        #         consultations_used = limit_check.get("consultations_used", 0)
        #         consultations_limit = limit_check.get("consultations_limit", 3)
        #         payment_link = subscription_service.get_payment_link(str(user_id))
        #
        #         limit_msg = f"""❌ *Limite de consultas gratuitas atingido*
        #
        # Você usou suas {consultations_limit} consultas gratuitas.
        #
        # 🚀 *Plano Professional - R$ 190/mês*
        # ✅ Prontuários ilimitados
        # ✅ Transcrição em tempo real
        # ✅ Templates personalizados
        # ✅ Suporte prioritário
        # ✅ Sem limites de uso
        #
        # 🔗 *Assine agora:*
        # {payment_link}
        #
        # 💡 Faça upgrade para continuar usando o ProntoDoc!"""
        #
        #         send_telegram_message(BOT_TOKEN, chat_id, limit_msg)
        #         logger.warning(f"❌ User {user_id} blocked - Free tier limit exceeded ({consultations_used}/{consultations_limit})")
        #         return  # BLOCK PROCESSING
        #
        #     # Show warning if on last free consultation
        #     if limit_check.get("tier") == "free":
        #         remaining = limit_check.get("remaining", 0)
        #         if remaining <= 1:
        #             warning_msg = f"""⚠️ *Aviso: Esta é sua última consulta gratuita!*
        #
        # Após esta consulta, você precisará fazer upgrade para continuar usando.
        #
        # 🔗 Assine o plano Professional: {subscription_service.get_payment_link(str(user_id))}"""
        #             send_telegram_message(BOT_TOKEN, chat_id, warning_msg)

        # Use selected template or default to SOAP padrão
        selected_template = auth_service.get_selected_template(user_id)
        if not selected_template:
            # Use default SOAP template for immediate processing
            # ai_prompt_template is None so AI processor uses its comprehensive default SOAP prompt
            default_soap_template = {
                "id": "default-soap",
                "name": "SOAP padrão",
                "specialty": "Clínica Geral",
                "template_structure": {
                    "sections": [
                        {"name": "Queixa Principal", "required": True},
                        {"name": "História da Doença Atual", "required": True},
                        {"name": "Exame Físico", "required": True},
                        {"name": "Avaliação", "required": True},
                        {"name": "Plano Terapêutico", "required": True}
                    ]
                },
                "ai_prompt_template": None,  # Use AI processor's comprehensive default SOAP prompt
                "is_default": True,
                "is_public": True
            }
            selected_template = default_soap_template
            logger.info(f"🎵 Processing voice message for user {user_id} with default SOAP template (using AI processor's comprehensive prompt)")
        else:
            logger.info(f"🎵 Processing voice message for user {user_id} with selected template '{selected_template.get('name', 'Unknown')}')")

        # Get file info and download
        file_info = get_file_info(BOT_TOKEN, file_id)
        if not file_info:
            send_error_message(BOT_TOKEN, chat_id,
                error_type="file_processing",
                error_message="Não foi possível acessar o arquivo de áudio do Telegram",
                error_code="FILE_ACCESS_FAILED",
                details={
                    "file_id": file_id,
                    "telegram_api": "getFile failed"
                },
                suggestions=[
                    "Tente enviar o áudio novamente",
                    "Verifique se o arquivo não está corrompido",
                    "Use um arquivo de áudio menor (< 50MB)"
                ])
            return

        # Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_path = temp_file.name

        try:
            if not download_telegram_file(file_info["download_url"], temp_path):
                send_error_message(BOT_TOKEN, chat_id,
                    error_type="file_processing",
                    error_message="Falha no download do arquivo de áudio",
                    error_code="DOWNLOAD_FAILED",
                    details={
                        "file_size": f"{file_info.get('file_size', 'Unknown')} bytes",
                        "download_url": "Telegram file server",
                        "temp_path": temp_path
                    },
                    suggestions=[
                        "Verifique sua conexão com a internet",
                        "Tente enviar um áudio menor",
                        "Aguarde alguns minutos e tente novamente"
                    ])
                return

            # Send to AI service for processing
            send_telegram_message(BOT_TOKEN, chat_id, "🧠 Processando com IA...")

            # Create minimal patient data for AI service
            patient_data = {
                "full_name": "Paciente",
                "cpf": "00000000000",
                "pin": "0000"
            }

            result = await ai_service.process_consultation_direct(
                audio_file_path=temp_path,
                patient_data=patient_data,
                doctor_session=session,
                template=selected_template
            )

            if result.get("success"):
                # Send results with template info
                template_name = selected_template.get("name", "N/A")
                template_specialty = selected_template.get("specialty", "N/A")

                if result.get("transcription"):
                    send_telegram_message(BOT_TOKEN, chat_id,
                        f"📝 *Transcrição:*\n\n{result['transcription']}")

                if result.get("prontuario"):
                    prontuario_msg = f"📋 *Prontuário Médico:*\n"
                    prontuario_msg += f"🎯 Modelo: {template_name} ({template_specialty})\n\n"
                    prontuario_msg += result['prontuario']
                    send_telegram_message(BOT_TOKEN, chat_id, prontuario_msg)

                # ===== USAGE INCREMENT DISABLED - No usage tracking =====
                # if subscription_service:
                #     usage_result = await subscription_service.increment_usage(str(user_id), session)
                #     if usage_result.get("success"):
                #         logger.info(f"✅ Usage incremented for user {user_id}")
                #
                #         # Show remaining consultations for free tier users
                #         limit_check = await subscription_service.check_consultation_limit(str(user_id), session)
                #         if limit_check.get("tier") == "free":
                #             remaining = limit_check.get("remaining", 0)
                #             consultations_used = limit_check.get("consultations_used", 0)
                #             consultations_limit = limit_check.get("consultations_limit", 3)
                #
                #             if remaining > 0:
                #                 usage_msg = f"📊 Consulta {consultations_used}/{consultations_limit} - {remaining} restantes"
                #                 send_telegram_message(BOT_TOKEN, chat_id, usage_msg)

                # Mark processing as successful
                processing_success = True
                logger.info(f"✅ Successfully processed voice message for user {user_id} using template '{template_name}'")
            else:
                # Detailed AI processing error
                ai_error = result.get('error', 'Erro desconhecido no processamento de IA')

                # Determine error details based on the error message
                error_details = {
                    "ai_processor_url": ai_service.ai_processor_url,
                    "template_name": selected_template.get('name', 'N/A'),
                    "file_size": f"{file_info.get('file_size', 'Unknown')} bytes",
                    "user_id": str(user_id)
                }

                # Provide specific suggestions based on error type
                suggestions = [
                    "Verifique se o áudio está claro e audível",
                    "Tente com um áudio mais curto (< 10 minutos)",
                    "Aguarde alguns minutos e tente novamente",
                    "Verifique se selecionou o modelo correto com /templates"
                ]

                if "timeout" in ai_error.lower():
                    suggestions.insert(0, "O áudio pode estar muito longo para processamento")
                elif "network" in ai_error.lower() or "connection" in ai_error.lower():
                    suggestions.insert(0, "Problema de conexão com o servidor de IA")
                elif "auth" in ai_error.lower():
                    suggestions.insert(0, "Problema de autenticação - faça login novamente")

                send_error_message(BOT_TOKEN, chat_id,
                    error_type="ai_processing",
                    error_message=ai_error,
                    error_code="AI_PROCESSING_FAILED",
                    details=error_details,
                    suggestions=suggestions)

        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            # Mark processing as finished (successful or not)
            processing_state.finish_processing(file_id, success=processing_success)

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Determine error type and provide specific help
        error_type = "system"
        error_code = "VOICE_PROCESSING_FAILED"

        if "Permission" in str(e) or "access" in str(e).lower():
            error_type = "file_processing"
            error_code = "FILE_PERMISSION_ERROR"
        elif "timeout" in str(e).lower() or "ConnectionTimeout" in str(e):
            error_type = "network"
            error_code = "NETWORK_TIMEOUT"
        elif "Connection" in str(e) or "network" in str(e).lower():
            error_type = "network"
            error_code = "NETWORK_ERROR"

        send_error_message(BOT_TOKEN, chat_id,
            error_type=error_type,
            error_message=f"Erro inesperado durante o processamento de voz: {str(e)}",
            error_code=error_code,
            details={
                "exception_type": type(e).__name__,
                "user_id": str(user_id),
                "has_template": str(bool(auth_service.get_selected_template(user_id))),
                "session_active": str(bool(auth_service.get_doctor_session(user_id)))
            },
            suggestions=[
                "Tente fazer logout e login novamente",
                "Verifique sua conexão com a internet",
                "Use um áudio menor e mais claro",
                "Aguarde alguns minutos antes de tentar novamente"
            ])

        # Make sure processing state is cleared even on exception
        processing_state.finish_processing(file_id, success=False)

# WhatsApp Webhook Endpoints

@app.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    """Webhook verification for WhatsApp"""
    try:
        if not whatsapp_service.enabled:
            raise HTTPException(status_code=503, detail="WhatsApp not configured")

        # WhatsApp sends verification challenge
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')

        # Debug logging
        logger.info(f"🔍 WhatsApp webhook GET request: mode={mode}, token={token}, challenge={challenge}")
        logger.info(f"🔑 Expected token: {WEBHOOK_VERIFY_TOKEN}")

        # If no parameters, this might be a health check or test request
        if mode is None and token is None and challenge is None:
            logger.info("📋 GET request with no parameters - returning webhook info")
            return {"status": "WhatsApp webhook ready", "service": "doczap"}

        if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
            logger.info("✅ WhatsApp webhook verified successfully")
            return int(challenge)
        else:
            logger.error(f"❌ WhatsApp webhook verification failed - mode: {mode}, token_match: {token == WEBHOOK_VERIFY_TOKEN}")
            raise HTTPException(status_code=403, detail="Verification failed")

    except Exception as e:
        logger.error(f"WhatsApp webhook verification error: {e}")
        raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        if not whatsapp_service.enabled:
            logger.warning("WhatsApp service disabled but received POST webhook")
            return JSONResponse({"status": "whatsapp_disabled"})

        # Verify webhook signature (recommended for production)
        body = await request.body()
        signature = request.headers.get('X-Hub-Signature-256', '')

        if not verify_whatsapp_signature(body, signature):
            logger.warning("⚠️ WhatsApp webhook signature verification failed")

        # Parse webhook data
        data = await request.json()
        logger.info(f"📨 Received WhatsApp webhook POST: {data}")

        # Check if this is a real message or test
        is_test_data = False
        if data.get('entry'):
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        metadata = value.get('metadata', {})
                        phone_number_id = metadata.get('phone_number_id')
                        if phone_number_id in ['123456123', '15550559999']:  # Test IDs
                            is_test_data = True
                            logger.info("🧪 This is test data from Meta Dashboard")
                        else:
                            logger.info(f"📱 Real message from phone_number_id: {phone_number_id}")

        # Process webhook entry
        if data.get('object') == 'whatsapp_business_account':
            logger.info(f"📱 Processing WhatsApp business account webhook (test: {is_test_data})")
            for entry in data.get('entry', []):
                logger.info(f"📝 Processing entry: {entry.get('id', 'unknown')}")
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        logger.info(f"💬 Processing message change")
                        await process_whatsapp_message_change(change.get('value', {}))
                    else:
                        logger.info(f"📄 Skipping change field: {change.get('field')}")
        else:
            logger.warning(f"Unknown webhook object type: {data.get('object')}")

        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"WhatsApp webhook processing error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return JSONResponse({"status": "error", "message": str(e)})

def verify_whatsapp_signature(body: bytes, signature: str) -> bool:
    """Verify WhatsApp webhook signature"""
    app_secret = os.getenv('WHATSAPP_APP_SECRET', '')
    if not app_secret:
        logger.warning("WhatsApp app secret not configured - skipping signature verification")
        return True

    try:
        expected_signature = 'sha256=' + hmac.new(
            app_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"WhatsApp signature verification error: {e}")
        return False

async def process_whatsapp_message_change(value: Dict[str, Any]):
    """Process WhatsApp message change event"""
    try:
        # Extract message data
        messages = value.get('messages', [])
        for message in messages:
            await whatsapp_handler.handle_message(message)

        # Handle status updates (delivered, read, etc.)
        statuses = value.get('statuses', [])
        for status in statuses:
            # Log status updates
            status_type = status.get('status')
            message_id = status.get('id')
            recipient_id = status.get('recipient_id')
            logger.debug(f"WhatsApp message {message_id} status: {status_type} for {recipient_id}")

    except Exception as e:
        logger.error(f"WhatsApp message processing error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "service": "doczap-multi-platform",
        "telegram_enabled": bool(BOT_TOKEN),
        "whatsapp_enabled": whatsapp_service.enabled,
        "bot_running": True
    }

@app.get("/processing-stats")
async def get_processing_stats():
    """Get processing statistics for debugging (admin only in production)"""
    # Clean up old entries before returning stats
    processing_state.cleanup_old_entries()

    stats = processing_state.get_stats()
    return {
        "status": "ok",
        "processing": stats
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ProntoDoc Multi-Platform Bot",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)