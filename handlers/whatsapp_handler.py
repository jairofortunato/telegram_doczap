"""
WhatsApp Message Handler for DOCZAP
Processes WhatsApp messages using the same logic as Telegram
"""

import os
import tempfile
from typing import Dict, Any
from loguru import logger
from services.consultation_session_manager import get_session_manager

class WhatsAppHandler:
    def __init__(self, whatsapp_service, auth_service, ai_service, subscription_service=None, processing_state=None, image_service=None):
        self.whatsapp = whatsapp_service
        self.auth = auth_service
        self.ai = ai_service
        self.subscription = subscription_service
        self.processing_state = processing_state
        self.image_service = image_service

        # Initialize session manager for content accumulation
        self.session_manager = get_session_manager(timeout_minutes=30)
        logger.info("✅ WhatsApp handler initialized with session manager")

    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming WhatsApp message"""
        try:
            message_id = message.get('id')
            from_number = message.get('from')
            timestamp = message.get('timestamp')

            # Mark message as read
            await self.whatsapp.mark_as_read(message_id)

            # Use phone number as user ID (similar to Telegram user_id)
            user_id = from_number

            logger.info(f"📱 Processing WhatsApp message from {user_id}")

            # Handle different message types
            if 'text' in message:
                await self.handle_text_message(user_id, message['text']['body'])
            elif 'audio' in message:
                await self.handle_audio_message(user_id, message['audio'])
            elif 'voice' in message:
                await self.handle_audio_message(user_id, message['voice'])
            elif 'image' in message:
                await self.handle_image_message(user_id, message['image'])
            elif 'interactive' in message:
                await self.handle_interactive_message(user_id, message['interactive'])
            else:
                await self.whatsapp.send_text_message(
                    from_number,
                    "Desculpe, esse tipo de mensagem não é suportado. "
                    "Use texto, áudio ou imagem."
                )

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")

    async def handle_text_message(self, user_id: str, text: str):
        """Handle text messages (email/password flow or commands)"""
        try:
            text = text.strip()

            # Handle commands first
            if text.startswith('/') or text.lower() in ['início', 'start', 'oi', 'olá', 'menu', 'logout', 'sair', 'ajuda', 'help', 'status', 'situação', 'finalizar', 'nova consulta', 'novo paciente', 'fim', 'login', 'fazer login', 'cadastrar', 'criar conta', 'templates', 'modelos']:
                await self.handle_command(user_id, text)
                return

            # Handle template selection
            if text.lower().startswith('template '):
                await self.handle_template_selection(user_id, text)
                return

            # Handle templates list
            if text.lower() == 'templates':
                await self.handle_templates_command(user_id)
                return

            # Check if user is waiting to send password
            pending_login = self.auth.get_pending_login(user_id)

            if pending_login:
                # User is sending password
                email = pending_login["email"]
                password = text

                # Authenticate
                result = await self.auth.authenticate_doctor(user_id, email, password)

                # Clear pending login
                self.auth.clear_pending_login(user_id)

                if result.get("success"):
                    doctor_name = result["doctor"]["full_name"]
                    await self.whatsapp.send_text_message(
                        user_id,
                        f"✅ *Login Realizado com Sucesso!*\n\n"
                        f"Bem-vindo, Dr. {doctor_name}\n\n"
                        "✨ *Como usar o Prontodoc:*\n"
                        "• Envie áudios das consultas 🎙️\n"
                        "• Envie fotos de exames 📸\n"
                        "• Receba prontuários estruturados automaticamente\n\n"
                        "📋 Usando modelo: *Prontuário de Consulta Rápida (SOAP)*\n\n"
                        "💡 Digite *templates* para ver outros modelos\n"
                        "💡 Digite *ajuda* para ver todos os comandos")
                else:
                    await self.whatsapp.send_text_message(
                        user_id,
                        "❌ Senha incorreta\n\nEnvie *início* para tentar novamente")

            else:
                # Check if authenticated
                session = self.auth.get_doctor_session(user_id)
                if session:
                    await self.whatsapp.send_text_message(
                        user_id,
                        "🎙️ Envie um áudio para transcrever")
                    return

                # Treat as email (start login flow)
                if "@" in text and "." in text:
                    self.auth.start_login(user_id, text)
                    await self.whatsapp.send_text_message(user_id, "🔐 Agora envie sua senha")
                else:
                    await self.whatsapp.send_text_message(
                        user_id,
                        "❌ *Você precisa fazer login primeiro*\n\n"
                        "📧 Envie seu email para fazer login\n"
                        "🆕 Ou digite *início* para criar conta")

        except Exception as e:
            logger.error(f"Error handling WhatsApp text message: {e}")

    async def handle_command(self, user_id: str, command: str):
        """Handle commands and menu options"""
        try:
            command = command.lower().strip()

            if command in ['/start', 'início', 'start', 'oi', 'olá', 'menu']:
                await self.send_welcome_message(user_id)
            elif command in ['login', 'fazer login']:
                await self.send_login_instructions(user_id)
            elif command in ['cadastrar', 'criar conta']:
                await self.send_signup_link(user_id)
            elif command in ['templates', 'modelos']:
                await self.handle_templates_command(user_id)
            elif command in ['status', 'situação']:
                await self.handle_status_command(user_id)
            elif command in ['ajuda', 'help']:
                await self.send_help_message(user_id)
            elif command in ['logout', 'sair']:
                await self.handle_logout_command(user_id)
            elif command in ['finalizar', 'nova consulta', 'novo paciente', '/finalizar', 'fim']:
                await self.handle_finish_consultation(user_id)
            else:
                await self.send_main_menu(user_id)

        except Exception as e:
            logger.error(f"Error handling WhatsApp command: {e}")

    async def send_welcome_message(self, user_id: str):
        """Send welcome message"""
        # Check if already logged in
        session = self.auth.get_doctor_session(user_id)
        if session:
            await self.whatsapp.send_text_message(
                user_id,
                f"✅ Já logado como Dr. {session['full_name']}\n\n"
                "🎙️ Envie um áudio para transcrever")
            return

        welcome_text = """👋 *Bem-vindo ao Prontodoc!*

🤖 Assistente de prontuários médicos com IA

✨ *O que o Prontodoc faz:*
• Transcreve consultas em áudio
• Extrai resultados de exames
• Gera prontuários estruturados (SOAP)
• Integra tudo automaticamente

🔐 *Para começar:*

*Já tem conta?*
Envie seu email para fazer login

*Primeira vez?*
Crie sua conta gratuita:
https://prontuarioautomatico.vercel.app/signup

💡 Digite *ajuda* para ver todos os comandos"""

        await self.whatsapp.send_text_message(user_id, welcome_text)

    async def send_main_menu(self, user_id: str):
        """Send main menu options"""
        session = self.auth.get_doctor_session(user_id)

        if session:
            menu_text = """📋 *Menu Principal*

Você está logado. Escolha uma opção:"""

            buttons = [
                {"id": "templates", "title": "📋 Templates"},
                {"id": "logout", "title": "🚪 Logout"}
            ]
        else:
            menu_text = """📋 *Menu Principal*

Faça login ou crie sua conta:"""

            buttons = [
                {"id": "login", "title": "1️⃣ Login"},
                {"id": "cadastrar", "title": "2️⃣ Criar Conta"}
            ]

        await self.whatsapp.send_interactive_message(
            user_id,
            "Menu Prontodoc",
            menu_text,
            "Selecione uma opção",
            buttons
        )

    async def send_login_instructions(self, user_id: str):
        """Send login instructions"""
        login_text = """🔐 *Login no Prontodoc*

Para fazer login, envie sua mensagem no formato:

`login seu@email.com suasenha`

*Exemplo:*
`login dr.silva@hospital.com MinhaSenh@123`

💡 *Ainda não tem conta?*
Clique em *Criar Conta* abaixo."""

        buttons = [
            {"id": "cadastrar", "title": "2️⃣ Criar Conta"},
            {"id": "menu", "title": "📋 Menu Principal"}
        ]

        await self.whatsapp.send_interactive_message(
            user_id,
            "Login Prontodoc",
            login_text,
            "Precisa de ajuda?",
            buttons
        )

    async def send_signup_link(self, user_id: str):
        """Send signup link"""
        signup_text = """📝 *Criar Conta de Médico*

Para usar o Prontodoc, você precisa criar uma conta de médico na nossa plataforma.

🔗 *Link de Cadastro:*
👉 https://prontuarioautomatico.vercel.app/signup

*O que você pode fazer após criar sua conta:*
✅ Transcrição automática de consultas
✅ Geração de prontuários estruturados
✅ Modelos personalizados de consulta
✅ Histórico de atendimentos

*Após criar sua conta, volte aqui e faça login:*
`login seu@email.com suasenha`

💡 *Dica:* O cadastro é gratuito e leva apenas alguns minutos!"""

        buttons = [
            {"id": "login", "title": "🔐 Fazer Login"},
            {"id": "menu", "title": "📋 Menu Principal"}
        ]

        await self.whatsapp.send_interactive_message(
            user_id,
            "Criar Conta",
            signup_text,
            "Já tem conta?",
            buttons
        )


    async def handle_templates_command(self, user_id: str):
        """Handle templates command"""
        try:
            session = self.auth.get_doctor_session(user_id)
            if not session:
                await self.whatsapp.send_text_message(user_id, "❌ Faça login primeiro")
                return

            # Debug: Log session details
            logger.info(f"📋 [TEMPLATES] Fetching templates for doctor:")
            logger.info(f"   - User ID: {user_id}")
            logger.info(f"   - Profile ID: {session.get('profile_id')}")
            logger.info(f"   - Email: {session.get('email')}")
            logger.info(f"   - Has session_token: {bool(session.get('session_token'))}")
            if session.get('session_token'):
                logger.info(f"   - Token length: {len(session.get('session_token'))} chars")

            result = await self.ai.get_templates(session)

            if result.get("success"):
                templates = result.get("templates", [])

                # Debug: Log template details
                logger.info(f"📋 [TEMPLATES] Received {len(templates)} templates from API")
                for i, template in enumerate(templates, 1):
                    logger.info(f"   {i}. {template.get('name')} ({template.get('specialty')})")
                    logger.info(f"      - is_public: {template.get('is_public')}")
                    logger.info(f"      - is_default: {template.get('is_default')}")
                    logger.info(f"      - created_by: {template.get('created_by')}")

                if not templates:
                    await self.whatsapp.send_text_message(user_id, "❌ Nenhum modelo encontrado")
                    return

                templates_msg = "📋 *Modelos:*\n\n"

                for i, template in enumerate(templates[:10], 1):
                    name = template.get("name", "N/A")
                    specialty = template.get("specialty", "N/A")
                    templates_msg += f"{i}. {name} - {specialty}\n"

                templates_msg += "\n💡 Envie: template 1"

                await self.whatsapp.send_text_message(user_id, templates_msg)

                # Store templates for selection
                if user_id in self.auth.active_sessions:
                    self.auth.active_sessions[user_id]["available_templates"] = templates

            else:
                await self.whatsapp.send_text_message(user_id, "❌ Erro ao buscar modelos")

        except Exception as e:
            logger.error(f"WhatsApp templates error: {e}")
            await self.whatsapp.send_text_message(user_id, "❌ Erro ao buscar modelos")

    async def handle_template_selection(self, user_id: str, command: str):
        """Handle template selection"""
        try:
            parts = command.split()
            if len(parts) != 2:
                await self.whatsapp.send_text_message(user_id, "❌ Use: template 1")
                return

            try:
                template_number = int(parts[1])
            except ValueError:
                await self.whatsapp.send_text_message(user_id, "❌ Número inválido")
                return

            session = self.auth.get_doctor_session(user_id)
            if not session:
                await self.whatsapp.send_text_message(user_id, "❌ Faça login primeiro")
                return

            available_templates = session.get("available_templates", [])
            if not available_templates:
                await self.whatsapp.send_text_message(user_id, "❌ Use *templates* primeiro")
                return

            if template_number < 1 or template_number > len(available_templates):
                await self.whatsapp.send_text_message(
                    user_id,
                    f"❌ Escolha entre 1 e {len(available_templates)}")
                return

            selected_template = available_templates[template_number - 1]
            template_name = selected_template.get("name", "N/A")

            # Set selected template
            self.auth.set_selected_template(user_id, selected_template)

            await self.whatsapp.send_text_message(
                user_id,
                f"✅ Modelo selecionado: {template_name}\n\n"
                "🎙️ Envie um áudio da consulta")

        except Exception as e:
            logger.error(f"Template selection error: {e}")
            await self.whatsapp.send_text_message(user_id, "❌ Erro ao selecionar modelo")

    async def handle_audio_message(self, user_id: str, audio: Dict[str, Any]):
        """Handle audio/voice messages"""
        # Get media ID for deduplication
        media_id = audio.get('id')
        if not media_id:
            logger.error("❌ Audio message missing media ID - cannot process")
            return

        # Check if this audio is already being processed or was recently completed
        if self.processing_state:
            if self.processing_state.is_processing(media_id):
                logger.warning(f"⚠️ WhatsApp audio {media_id} is already being processed - ignoring duplicate")
                return

            if self.processing_state.is_completed(media_id):
                logger.warning(f"⚠️ WhatsApp audio {media_id} was already processed recently - ignoring duplicate")
                return

            # Mark as processing - prevent duplicate processing
            if not self.processing_state.start_processing(media_id):
                logger.warning(f"⚠️ WhatsApp audio {media_id} could not be marked for processing - skipping")
                return

        processing_success = False
        try:
            # Check if user is authenticated
            session = self.auth.get_doctor_session(user_id)
            if not session:
                await self.send_welcome_message(user_id)
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            # ===== SUBSCRIPTION CHECK - Check consultation limit before processing =====
            if not self.subscription:
                logger.error(f"❌ Subscription service not initialized - BLOCKING ACCESS for user {user_id}")
                await self.whatsapp.send_text_message(
                    user_id,
                    "❌ Sistema de verificação indisponível. Entre em contato com o suporte."
                )
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            # Get profile user_id from session
            profile_user_id = session.get('user_id') or session.get('profile_id')

            if not profile_user_id:
                logger.error(f"❌ No user_id found in session for WhatsApp user {user_id} - blocking access")
                await self.whatsapp.send_text_message(
                    user_id,
                    "❌ Erro: Sessão inválida. Faça logout e login novamente."
                )
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            limit_check = await self.subscription.check_consultation_limit_direct(profile_user_id)

            if not limit_check.get("can_create", False):
                # FREE TIER LIMIT EXCEEDED - Create checkout session and send link
                consultations_used = limit_check.get("consultations_used", 0)
                consultations_limit = limit_check.get("consultations_limit", 5)

                # Get user email from session
                user_email = session.get('email', '')
                user_phone = user_id  # WhatsApp phone number

                # Create Stripe checkout session
                checkout_result = await self.subscription.create_checkout_session(
                    profile_user_id,
                    user_email,
                    user_phone
                )

                if checkout_result.get("success"):
                    checkout_url = checkout_result.get("checkout_url")

                    limit_msg = f"""❌ *Limite de consultas gratuitas atingido*

Você usou suas {consultations_limit} consultas gratuitas.

🚀 *Plano Professional - R$ 190/mês*
✅ Prontuários ilimitados
✅ Transcrição em tempo real
✅ Templates personalizados
✅ Suporte prioritário

🔗 *Assine agora:*
{checkout_url}

💡 *Dica:* Com o Professional, você pode criar quantos prontuários quiser sem limites!"""
                else:
                    # Fallback to web app if checkout creation fails
                    web_app_url = self.subscription.web_app_url
                    limit_msg = f"""❌ *Limite de consultas gratuitas atingido*

Você usou suas {consultations_limit} consultas gratuitas.

🚀 *Plano Professional - R$ 190/mês*
✅ Prontuários ilimitados
✅ Transcrição em tempo real
✅ Templates personalizados
✅ Suporte prioritário

🔗 *Assine agora:*
{web_app_url}/doctor/configuracoes

💡 *Dica:* Com o Professional, você pode criar quantos prontuários quiser sem limites!"""

                buttons = [
                    {"id": "status", "title": "📊 Ver Status"},
                    {"id": "menu", "title": "📋 Menu"}
                ]

                await self.whatsapp.send_interactive_message(
                    user_id,
                    "Upgrade Necessário",
                    limit_msg,
                    "Próximas ações",
                    buttons
                )

                # Mark processing as finished
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            # Use selected template or default to SOAP padrão
            selected_template = self.auth.get_selected_template(user_id)
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
                logger.info(f"🎵 Processing WhatsApp audio for user {user_id} with default SOAP template (using AI processor's comprehensive prompt)")
            else:
                logger.info(f"🎵 Processing WhatsApp audio for user {user_id} with selected template '{selected_template.get('name', 'Unknown')}')")

            await self.whatsapp.send_text_message(
                user_id,
                "✅ Áudio recebido. Processando..."
            )

            # Download audio (media_id already extracted at function start)
            audio_data = await self.whatsapp.download_media(media_id)

            if not audio_data:
                await self.whatsapp.send_text_message(
                    user_id,
                    "❌ Erro ao baixar áudio. Tente novamente."
                )
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            try:
                # ===== NEW SESSION-BASED APPROACH =====
                # Step 1: Transcribe audio only (don't generate prontuário yet)
                await self.whatsapp.send_text_message(
                    user_id,
                    "🎙️ Transcrevendo áudio..."
                )

                # Call ai-processor just for transcription
                import httpx
                ai_processor_url = os.getenv(
                    'AI_PROCESSOR_URL',
                    'https://saude-ai-processor-production-bebd.up.railway.app'
                )

                async with httpx.AsyncClient(timeout=120.0) as client:
                    with open(temp_path, 'rb') as audio_file:
                        files = {'audio': ('audio.ogg', audio_file, 'audio/ogg')}
                        data = {'language': 'pt-BR'}

                        response = await client.post(
                            f"{ai_processor_url}/api/telegram/transcribe-only",
                            files=files,
                            data=data,
                            timeout=120.0
                        )

                if response.status_code != 200:
                    await self.whatsapp.send_text_message(
                        user_id,
                        f"❌ Erro na transcrição (código {response.status_code})"
                    )
                    if self.processing_state:
                        self.processing_state.finish_processing(media_id, success=False)
                    return

                transcription_result = response.json()
                if not transcription_result.get("success"):
                    await self.whatsapp.send_text_message(
                        user_id,
                        f"❌ {transcription_result.get('error', 'Erro na transcrição')}"
                    )
                    if self.processing_state:
                        self.processing_state.finish_processing(media_id, success=False)
                    return

                transcript = transcription_result.get("transcript", "")
                duration = transcription_result.get("duration", 0)

                # Step 2: Get or create session
                consultation_session = self.session_manager.get_or_create_session(user_id, session)

                # Check if this is a fresh session (no content yet)
                is_new_session = len(consultation_session.audio_transcripts) == 0 and len(consultation_session.image_extractions) == 0

                # Store patient info and template if this is the first content
                if not consultation_session.patient_name:
                    consultation_session.patient_name = "Paciente"
                if not consultation_session.template:
                    consultation_session.template = selected_template
                    consultation_session.template_name = selected_template.get("name", "SOAP padrão")
                    consultation_session.template_specialty = selected_template.get("specialty", "Clínica Geral")

                # Step 3: Add transcript to session
                consultation_session.add_audio_transcript(transcript, duration)

                # Notify user if this is a new consultation
                if is_new_session:
                    new_consultation_msg = f"""🆕 *Nova Consulta Iniciada*

📋 Modelo: {consultation_session.template_name}
🏥 Especialidade: {consultation_session.template_specialty}

✨ *Como usar:*
• Envie áudios da consulta 🎙️
• Envie fotos de exames 📸
• Tudo será integrado no prontuário automaticamente

💡 Digite *finalizar* quando terminar esta consulta"""
                    await self.whatsapp.send_text_message(user_id, new_consultation_msg)

                # Step 4: Regenerate prontuário from ALL session content
                await self.whatsapp.send_text_message(
                    user_id,
                    "🧠 Gerando prontuário..."
                )

                regen_result = await self.regenerate_prontuario_from_session(user_id, session)

                if regen_result.get("success"):
                    template_name = selected_template.get("name", "N/A")
                    template_specialty = selected_template.get("specialty", "N/A")

                    prontuario = regen_result.get("prontuario", "")

                    # Send prontuario (not saved to database - just in session memory)
                    if prontuario:
                        prontuario_msg = f"📋 *Prontuário Médico:*\n"
                        prontuario_msg += f"🎯 *Modelo:* {template_name} ({template_specialty})\n\n"
                        prontuario_msg += prontuario
                        await self.whatsapp.send_text_message(user_id, prontuario_msg)

                    # Increment usage counter for new consultations (free tier only)
                    if is_new_session and self.subscription:
                        profile_user_id = session.get('user_id') or session.get('profile_id')
                        if profile_user_id:
                            # Check if user is on free tier before incrementing
                            tier_check = await self.subscription.check_consultation_limit_direct(profile_user_id)
                            if tier_check.get("tier") == "free":
                                increment_result = await self.subscription.increment_usage_direct(profile_user_id)
                                if increment_result.get("success"):
                                    logger.info(f"✅ Usage incremented for user {profile_user_id} - now at {increment_result.get('consultations_used', 'unknown')}")
                                else:
                                    logger.warning(f"⚠️ Failed to increment usage for user {profile_user_id}: {increment_result.get('error')}")

                    # Send success message with session info and action buttons
                    session_summary = consultation_session.get_summary()

                    # Contextual message: encourage images on first audio if none sent yet
                    if session_summary['audio_count'] == 1 and session_summary['image_count'] == 0:
                        success_msg = (
                            "✅ *Prontuário Criado*\n\n"
                            f"📊 Áudios: {session_summary['audio_count']}\n"
                            f"📸 Imagens: {session_summary['image_count']}\n\n"
                            "📸 *Dica:* Você pode enviar fotos de exames!\n"
                            "Hemogramas, laudos, receitas... O prontuário será automaticamente atualizado.\n\n"
                            "💡 Ou continue enviando áudios para adicionar mais informações"
                        )
                    else:
                        success_msg = (
                            "✅ *Prontuário Atualizado*\n\n"
                            f"📊 Áudios: {session_summary['audio_count']}\n"
                            f"📸 Imagens: {session_summary['image_count']}\n\n"
                            "💡 Envie mais áudios ou imagens para adicionar informações"
                        )

                    buttons = [
                        {"id": "finalizar", "title": "🏁 Finalizar Consulta"},
                        {"id": "templates", "title": "📋 Trocar Modelo"}
                    ]

                    await self.whatsapp.send_interactive_message(
                        user_id,
                        "Prontuário Pronto",
                        success_msg,
                        "O que deseja fazer?",
                        buttons
                    )

                    # Mark processing as successful
                    processing_success = True
                    logger.info(f"✅ Successfully processed WhatsApp audio {media_id} for user {user_id}")
                else:
                    error_msg = f"❌ Erro ao gerar prontuário: {regen_result.get('error', 'Erro desconhecido')}"
                    await self.whatsapp.send_text_message(user_id, error_msg)

            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

                # Mark processing as finished
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=processing_success)

        except Exception as e:
            logger.error(f"WhatsApp audio processing error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            await self.whatsapp.send_text_message(
                user_id,
                "❌ Erro ao processar áudio. Tente novamente."
            )

            # Make sure processing state is cleared even on exception
            if self.processing_state:
                self.processing_state.finish_processing(media_id, success=False)

    async def handle_image_message(self, user_id: str, image: Dict[str, Any]):
        """Handle image messages - extract text and add to last prontuário"""
        # Get media ID for deduplication
        media_id = image.get('id')
        if not media_id:
            logger.error("❌ Image message missing media ID - cannot process")
            return

        # Check if this image is already being processed or was recently completed
        if self.processing_state:
            if self.processing_state.is_processing(media_id):
                logger.warning(f"⚠️ WhatsApp image {media_id} is already being processed - ignoring duplicate")
                return

            if self.processing_state.is_completed(media_id):
                logger.warning(f"⚠️ WhatsApp image {media_id} was already processed recently - ignoring duplicate")
                return

            # Mark as processing - prevent duplicate processing
            if not self.processing_state.start_processing(media_id):
                logger.warning(f"⚠️ WhatsApp image {media_id} could not be marked for processing - skipping")
                return

        processing_success = False
        try:
            # Check if user is authenticated
            session = self.auth.get_doctor_session(user_id)
            if not session:
                await self.send_welcome_message(user_id)
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            # Check if image service is available
            if not self.image_service:
                await self.whatsapp.send_text_message(
                    user_id,
                    "❌ Serviço de processamento de imagens não disponível."
                )
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            # ===== SUBSCRIPTION CHECK FOR IMAGES =====
            # Images are part of the same consultation session, so we need to check
            # if the user has an active session (which means they already passed the check for audio)
            consultation_session = self.session_manager.get_session(user_id)

            if not consultation_session:
                # No active session - user needs to send audio first (which checks subscription)
                await self.whatsapp.send_text_message(
                    user_id,
                    "⚠️ Por favor, envie primeiro um áudio da consulta.\n\n"
                    "As imagens serão integradas ao prontuário da consulta ativa."
                )
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            await self.whatsapp.send_text_message(
                user_id,
                "📸 Imagem recebida. Processando..."
            )

            # Download image
            image_data = await self.whatsapp.download_media(media_id)

            if not image_data:
                await self.whatsapp.send_text_message(
                    user_id,
                    "❌ Erro ao baixar imagem. Tente novamente."
                )
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            await self.whatsapp.send_text_message(
                user_id,
                "🔍 Extraindo informações da imagem..."
            )

            # ===== NEW SESSION-BASED APPROACH =====
            # Step 1: Extract text from image
            extraction_result = await self.image_service.extract_text_from_image(image_data)

            if not extraction_result.get("success"):
                error_msg = f"❌ {extraction_result.get('error', 'Erro ao processar imagem')}"
                await self.whatsapp.send_text_message(user_id, error_msg)
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=False)
                return

            extracted_text = extraction_result["extracted_text"]

            # Send raw transcription of the image
            transcription_msg = f"""📄 *Transcrição da Imagem:*

{extracted_text}"""

            await self.whatsapp.send_text_message(user_id, transcription_msg)

            # Step 2: Check if there's an active session (need at least one audio first)
            consultation_session = self.session_manager.get_session(user_id)

            if not consultation_session:
                # No session exists - user needs to send audio first
                info_msg = """💡 *Informação:*

A transcrição foi extraída com sucesso!

⚠️ Para criar um prontuário completo, primeiro envie um áudio da consulta."""

                await self.whatsapp.send_text_message(user_id, info_msg)
                logger.info(f"✅ Image transcribed for user {user_id} (no active session)")

                # Mark processing as finished (transcription only, no session to update)
                if self.processing_state:
                    self.processing_state.finish_processing(media_id, success=True)
                return

            # Step 3: Add image extraction to session
            consultation_session.add_image_extraction(extracted_text)

            # Debug: verify image was added
            print(f"\n📸 [DEBUG] Image extraction added to session")
            print(f"   User: {user_id}")
            print(f"   Extracted text length: {len(extracted_text)} chars")
            print(f"   Total images in session: {len(consultation_session.image_extractions)}")
            print(f"   Total audios in session: {len(consultation_session.audio_transcripts)}")
            print(f"   Extracted text preview: {extracted_text[:200]}...\n")

            # Step 4: Regenerate prontuário from ALL session content (audios + images)
            await self.whatsapp.send_text_message(
                user_id,
                "🔄 Atualizando prontuário com as informações da imagem..."
            )

            regen_result = await self.regenerate_prontuario_from_session(user_id, session)

            if regen_result.get("success"):
                prontuario = regen_result.get("prontuario", "")
                template_name = consultation_session.template_name

                # Send updated prontuario (not saved to database - just in session memory)
                if prontuario:
                    prontuario_msg = f"📋 *Prontuário Atualizado:*\n"
                    prontuario_msg += f"🎯 *Modelo:* {template_name}\n\n"
                    prontuario_msg += prontuario
                    await self.whatsapp.send_text_message(user_id, prontuario_msg)

                # Send success message with session info and action buttons
                session_summary = consultation_session.get_summary()
                success_msg = (
                    "✅ *Prontuário Atualizado com Exame!*\n\n"
                    f"📊 Áudios: {session_summary['audio_count']}\n"
                    f"📸 Imagens: {session_summary['image_count']}\n\n"
                    "📋 Os resultados do exame foram integrados ao prontuário.\n\n"
                    "💡 Envie mais exames ou áudios para adicionar informações"
                )

                buttons = [
                    {"id": "finalizar", "title": "🏁 Finalizar Consulta"},
                    {"id": "templates", "title": "📋 Trocar Modelo"}
                ]

                await self.whatsapp.send_interactive_message(
                    user_id,
                    "Prontuário Atualizado",
                    success_msg,
                    "O que deseja fazer?",
                    buttons
                )

                # Mark processing as successful
                processing_success = True
                logger.info(f"✅ Successfully processed image and regenerated prontuário for user {user_id}")
            else:
                error_msg = f"❌ {regen_result.get('error', 'Erro ao atualizar prontuário')}"
                await self.whatsapp.send_text_message(user_id, error_msg)

            # Mark processing as finished
            if self.processing_state:
                self.processing_state.finish_processing(media_id, success=processing_success)

        except Exception as e:
            logger.error(f"WhatsApp image processing error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            await self.whatsapp.send_text_message(
                user_id,
                "❌ Erro ao processar imagem. Tente novamente."
            )

            # Make sure processing state is cleared even on exception
            if self.processing_state:
                self.processing_state.finish_processing(media_id, success=False)

    async def handle_interactive_message(self, user_id: str, interactive: Dict[str, Any]):
        """Handle button/interactive message responses"""
        try:
            if interactive.get('type') == 'button_reply':
                button_id = interactive['button_reply']['id']

                if button_id == 'login':
                    await self.send_login_instructions(user_id)
                elif button_id == 'cadastrar':
                    await self.send_signup_link(user_id)
                elif button_id == 'ajuda':
                    await self.send_help_message(user_id)
                elif button_id == 'templates':
                    await self.handle_templates_command(user_id)
                elif button_id == 'status':
                    await self.handle_status_command(user_id)
                elif button_id == 'logout':
                    await self.handle_logout_command(user_id)
                elif button_id == 'finalizar':
                    await self.handle_finish_consultation(user_id)
                elif button_id == 'menu':
                    await self.send_main_menu(user_id)
                else:
                    await self.send_main_menu(user_id)

        except Exception as e:
            logger.error(f"WhatsApp interactive message error: {e}")

    async def handle_status_command(self, user_id: str):
        """Handle status command"""
        session = self.auth.get_doctor_session(user_id)

        if session:
            doctor_name = session.get("full_name", "N/A")
            selected_template = self.auth.get_selected_template(user_id)

            if selected_template:
                template_name = selected_template.get("name", "N/A")
                template_specialty = selected_template.get("specialty", "N/A")
                template_info = f"📋 Modelo: {template_name}\n🏥 Especialidade: {template_specialty}"
            else:
                template_info = "📋 Modelo: Prontuário de Consulta Rápida (SOAP)\n🏥 Especialidade: Clínica Geral"

            # Check if there's an active consultation
            consultation_session = self.session_manager.get_session(user_id)
            if consultation_session:
                session_summary = consultation_session.get_summary()
                consultation_info = f"\n\n📊 *Consulta em andamento:*\n• Áudios: {session_summary['audio_count']}\n• Imagens: {session_summary['image_count']}\n• Duração: {session_summary['duration_minutes']:.1f} min"
            else:
                consultation_info = "\n\n💡 Nenhuma consulta em andamento"

            status_msg = f"""✅ *Status do Prontodoc*

👤 Dr. {doctor_name}
{template_info}{consultation_info}

🎙️ Envie áudio para continuar ou iniciar nova consulta"""

            await self.whatsapp.send_text_message(user_id, status_msg)
        else:
            await self.whatsapp.send_text_message(
                user_id,
                "❌ Não logado\n\nEnvie *início* para começar")

    async def handle_logout_command(self, user_id: str):
        """Handle logout command"""
        self.auth.logout(user_id)
        self.auth.clear_pending_login(user_id)
        await self.whatsapp.send_text_message(user_id, "✅ Logout realizado")

    async def handle_finish_consultation(self, user_id: str):
        """Finish current consultation and prepare for new one"""
        session = self.auth.get_doctor_session(user_id)
        if not session:
            await self.whatsapp.send_text_message(
                user_id,
                "❌ Você não está logado."
            )
            return

        # Get current consultation session
        consultation_session = self.session_manager.get_session(user_id)

        if not consultation_session:
            await self.whatsapp.send_text_message(
                user_id,
                "ℹ️ Nenhuma consulta ativa no momento."
            )
            return

        # Get summary before ending
        summary = consultation_session.get_summary()

        # End the session
        self.session_manager.end_session(user_id)

        # Send confirmation with summary
        confirmation_msg = f"""✅ *Consulta Finalizada com Sucesso*

📊 *Resumo desta consulta:*
• Áudios processados: {summary['audio_count']}
• Exames integrados: {summary['image_count']}
• Duração total: {summary['duration_minutes']:.1f} minutos

🆕 *Pronto para nova consulta!*
Envie um áudio para iniciar o próximo atendimento."""

        await self.whatsapp.send_text_message(user_id, confirmation_msg)

    async def send_help_message(self, user_id: str):
        """Send help message"""
        help_text = """*Comandos:*

início - Iniciar
status - Ver status
templates - Ver modelos
finalizar - Finalizar consulta atual
logout - Sair

*Como usar:*
1. Envie seu email
2. Envie sua senha
3. Envie áudio da consulta
4. Receba transcrição + prontuário
5. Digite *finalizar* para nova consulta"""

        await self.whatsapp.send_text_message(user_id, help_text)

    async def regenerate_prontuario_from_session(self, user_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regenerate prontuário from all accumulated content in session
        This is called after each audio or image to create a fresh prontuário with all context
        """
        try:
            consultation_session = self.session_manager.get_session(user_id)
            if not consultation_session:
                return {"success": False, "error": "No active session"}

            # Get all accumulated content
            accumulated_content = consultation_session.get_accumulated_content()

            if not accumulated_content.strip():
                return {"success": False, "error": "No content to process"}

            logger.info(f"🔄 Regenerating prontuário from session content ({len(accumulated_content)} chars)")
            logger.info(f"📊 Session stats - Audios: {len(consultation_session.audio_transcripts)}, Images: {len(consultation_session.image_extractions)}")
            logger.info(f"📝 Accumulated content preview:\n{accumulated_content[:500]}...")

            # Debug: print full accumulated content
            print(f"\n{'='*80}")
            print(f"🔍 [DEBUG] ACCUMULATED CONTENT FOR PRONTUÁRIO GENERATION")
            print(f"{'='*80}")
            print(f"📊 Audios: {len(consultation_session.audio_transcripts)}")
            print(f"📸 Images: {len(consultation_session.image_extractions)}")
            print(f"📏 Total length: {len(accumulated_content)} chars")
            print(f"{'='*80}")
            print(accumulated_content)
            print(f"{'='*80}\n")

            # Use selected template or default
            template = consultation_session.template or {
                "name": "SOAP padrão",
                "specialty": "Clínica Geral",
                "ai_prompt_template": None
            }

            # Call ai-processor to generate prontuário from accumulated content
            import httpx
            ai_processor_url = os.getenv(
                'AI_PROCESSOR_URL',
                'https://saude-ai-processor-production-bebd.up.railway.app'
            )

            async with httpx.AsyncClient(timeout=120.0) as client:
                # Create a prompt that instructs GPT-4o to generate prontuário from accumulated content
                payload = {
                    "transcript": accumulated_content,
                    "patient_name": consultation_session.patient_name or "Paciente",
                    "template_name": template.get("name", "SOAP padrão"),
                    "template_specialty": template.get("specialty", "Clínica Geral"),
                    "ai_prompt_template": template.get("ai_prompt_template")
                }

                # Debug: log API payload
                print(f"\n🌐 [DEBUG] Sending to AI Processor:")
                print(f"   URL: {ai_processor_url}/api/telegram/generate-prontuario")
                print(f"   Patient: {payload['patient_name']}")
                print(f"   Template: {payload['template_name']}")
                print(f"   Transcript length: {len(payload['transcript'])} chars")
                print(f"   Transcript preview: {payload['transcript'][:300]}...\n")

                response = await client.post(
                    f"{ai_processor_url}/api/telegram/generate-prontuario",
                    json=payload,
                    timeout=120.0
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        prontuario = result.get("prontuario", "")
                        consultation_session.set_prontuario(prontuario)
                        logger.info(f"✅ Prontuário regenerated successfully ({len(prontuario)} chars)")
                        return {"success": True, "prontuario": prontuario}
                    else:
                        return {"success": False, "error": result.get("error", "Generation failed")}
                else:
                    return {"success": False, "error": f"AI processor returned {response.status_code}"}

        except Exception as e:
            logger.error(f"❌ Error regenerating prontuário: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}