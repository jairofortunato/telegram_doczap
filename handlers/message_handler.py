"""
Message Handlers for DocZap Telegram Bot
Handles all Telegram message types and commands
"""

import os
import tempfile
import time
from typing import Dict, Any
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from loguru import logger
import aiofiles

from utils.audio_utils import convert_audio_to_wav, get_audio_duration
from services.auth_service import AuthService
from services.ai_service import AIService

class MessageHandlers:
    def __init__(self, auth_service: AuthService, ai_service: AIService):
        self.auth_service = auth_service
        self.ai_service = ai_service

        # Default patient data for all users (simplified for testing)
        self.default_patient = {
            "profile_id": "default-patient-001",
            "full_name": "Paciente de Teste",
            "cpf": "000.000.000-00",
            "pin": "123456"
        }

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        try:
            user_id = update.effective_user.id

            welcome_message = (
                "🏥 **Bem-vindo ao DocZap!**\n\n"
                "Sou seu assistente médico para transcrição de consultas.\n\n"
                "**Para começar:**\n"
                "1. Use /login para autenticar como médico\n"
                "2. Envie mensagens de voz para transcrever consultas\n\n"
                "🎙️ **Funcionalidades:**\n"
                "• Transcrição automática com OpenAI Whisper\n"
                "• Geração de prontuário estruturado com GPT-4o\n"
                "• Formato SOAP (Subjetivo, Objetivo, Avaliação, Plano)\n\n"
                "Digite /help para ver todos os comandos disponíveis."
            )

            await update.message.reply_text(welcome_message, parse_mode='Markdown')
            logger.info(f"👋 User {user_id} started bot")

        except Exception as error:
            logger.error(f"❌ Error in /start: {error}")
            await update.message.reply_text("❌ Erro interno. Tente novamente.")

    async def handle_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /login command"""
        try:
            user_id = update.effective_user.id

            # Check if already authenticated
            if self.auth_service.is_authenticated(user_id):
                session = self.auth_service.get_doctor_session(user_id)
                await update.message.reply_text(
                    f"✅ Você já está logado como Dr. {session['full_name']}"
                )
                return

            # Parse login command arguments
            args = context.args
            if len(args) != 2:
                await update.message.reply_text(
                    "❌ Uso correto: /login email senha\n"
                    "Exemplo: /login doctor@example.com minhasenha"
                )
                return

            email, password = args

            # Authenticate doctor
            auth_result = await self.auth_service.authenticate_doctor(user_id, email, password)

            if auth_result["success"]:
                doctor = auth_result["doctor"]
                await update.message.reply_text(
                    f"✅ Login realizado com sucesso!\n"
                    f"Bem-vindo, Dr. {doctor['full_name']}\n\n"
                    "🎙️ **Agora você pode enviar mensagens de voz para transcrever consultas!**\n\n"
                    "📋 O sistema irá:\n"
                    "• Transcrever o áudio automaticamente\n"
                    "• Gerar prontuário estruturado em formato SOAP\n"
                    "• Retornar tanto a transcrição quanto o prontuário"
                )
                logger.info(f"👨‍⚕️ Doctor authenticated: {doctor['full_name']}")
            else:
                await update.message.reply_text(f"❌ Erro no login: {auth_result['error']}")

        except Exception as error:
            logger.error(f"❌ Error in /login: {error}")
            await update.message.reply_text("❌ Erro interno no login. Tente novamente.")

    async def handle_logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /logout command"""
        try:
            user_id = update.effective_user.id

            if not self.auth_service.is_authenticated(user_id):
                await update.message.reply_text("❌ Você não está logado.")
                return

            self.auth_service.logout(user_id)

            await update.message.reply_text("🔓 Logout realizado com sucesso!")
            logger.info(f"🔓 User {user_id} logged out")

        except Exception as error:
            logger.error(f"❌ Error in /logout: {error}")
            await update.message.reply_text("❌ Erro interno no logout.")

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        try:
            help_text = (
                "🏥 **DocZap - Comandos Disponíveis**\n\n"
                "**Autenticação:**\n"
                "/login email senha - Fazer login como médico\n"
                "/logout - Fazer logout\n"
                "/status - Ver status da sessão\n\n"
                "**Transcrição:**\n"
                "🎙️ Envie mensagens de voz para processar\n"
                "📁 Envie arquivos de áudio\n\n"
                "**Outros:**\n"
                "/help - Mostrar esta ajuda\n"
                "/start - Reiniciar bot\n\n"
                "**Como usar:**\n"
                "1. Faça login com suas credenciais de médico\n"
                "2. Envie áudios das consultas para transcrição automática\n\n"
                "**O que o bot faz:**\n"
                "• Transcreve áudio com OpenAI Whisper\n"
                "• Gera prontuário estruturado com GPT-4o\n"
                "• Retorna transcrição + prontuário em formato SOAP"
            )

            await update.message.reply_text(help_text, parse_mode='Markdown')

        except Exception as error:
            logger.error(f"❌ Error in /help: {error}")
            await update.message.reply_text("❌ Erro ao mostrar ajuda.")

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            user_id = update.effective_user.id

            if not self.auth_service.is_authenticated(user_id):
                await update.message.reply_text("❌ Você não está logado. Use /login para autenticar.")
                return

            session = self.auth_service.get_doctor_session(user_id)

            status_text = (
                f"📊 **Status da Sessão**\n\n"
                f"👨‍⚕️ **Médico:** Dr. {session['full_name']}\n"
                f"📧 **Email:** {session['email']}\n"
                f"🕐 **Logado em:** {session['authenticated_at'].strftime('%d/%m/%Y %H:%M')}\n\n"
                f"👤 **Paciente:** {self.default_patient['full_name']}\n\n"
                "✅ **Pronto para transcrever consultas!**\n\n"
                "🎙️ Envie mensagens de voz para:\n"
                "• Transcrever automaticamente com Whisper\n"
                "• Gerar prontuário estruturado com GPT-4o"
            )

            await update.message.reply_text(status_text, parse_mode='Markdown')

        except Exception as error:
            logger.error(f"❌ Error in /status: {error}")
            await update.message.reply_text("❌ Erro ao verificar status.")


    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages - simplified"""
        try:
            user_id = update.effective_user.id

            # Check if authenticated
            if not self.auth_service.is_authenticated(user_id):
                await update.message.reply_text(
                    "❌ Você precisa estar logado primeiro.\n"
                    "Use: /login email senha"
                )
                return

            # Simple response for any text
            await update.message.reply_text(
                "ℹ️ **DocZap está pronto!**\n\n"
                "🎙️ Para processar consultas, envie mensagens de voz.\n\n"
                "Use /help para ver comandos disponíveis."
            )

        except Exception as error:
            logger.error(f"❌ Error handling text message: {error}")
            await update.message.reply_text("❌ Erro ao processar mensagem.")

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle voice messages"""
        await self._process_audio(update, context, update.message.voice, "voice")

    async def handle_audio_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle audio files"""
        await self._process_audio(update, context, update.message.audio, "audio")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle documents (audio files sent as documents)"""
        document = update.message.document

        # Check if it's an audio file
        if document.mime_type and document.mime_type.startswith('audio/'):
            await self._process_audio(update, context, document, "document")
        else:
            await update.message.reply_text(
                "❌ Por favor, envie apenas arquivos de áudio para transcrição."
            )

    async def _process_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE, audio_obj, audio_type: str) -> None:
        """Process audio messages/files"""
        try:
            user_id = update.effective_user.id

            # Check authentication
            if not self.auth_service.is_authenticated(user_id):
                await update.message.reply_text(
                    "❌ Você precisa estar logado para usar a transcrição.\n"
                    "Use: /login email senha"
                )
                return

            doctor_session = self.auth_service.get_doctor_session(user_id)
            patient_data = self.default_patient  # Use default patient for simplicity

            # Send processing message
            processing_msg = await update.message.reply_text("🎙️ Processando áudio...")

            # Download audio file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_path = temp_file.name

                try:
                    # Download audio
                    audio_file = await audio_obj.get_file()
                    await audio_file.download_to_drive(temp_path)

                    # Get audio duration for user feedback
                    duration = get_audio_duration(temp_path)

                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=processing_msg.message_id,
                        text=f"🎙️ Transcrevendo áudio ({duration:.1f}s)..."
                    )

                    # Process consultation
                    result = await self.ai_service.process_consultation(
                        temp_path,
                        patient_data,
                        doctor_session
                    )

                    if result["success"]:
                        transcription = result.get('transcription', '')
                        prontuario = result.get('prontuario', '')
                        processing_time = result.get('processing_time', 0)
                        template_info = result.get('template', {})

                        # Send transcription first
                        transcription_text = (
                            "🎙️ **TRANSCRIÇÃO**\n\n"
                            f"👤 **Paciente:** {patient_data['full_name']}\n"
                            f"⏱️ **Duração:** {result.get('duration', 'N/A')}\n"
                            f"🕐 **Tempo de processamento:** {processing_time:.1f}s\n\n"
                            f"**Texto transcrito:**\n\n"
                            f"{transcription}"
                        )

                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=processing_msg.message_id,
                            text=transcription_text,
                            parse_mode='Markdown'
                        )

                        # Send prontuário as a separate message
                        if prontuario:
                            prontuario_text = (
                                "📋 **PRONTUÁRIO MÉDICO**\n\n"
                                f"👤 **Paciente:** {patient_data['full_name']}\n"
                                f"📅 **Data:** {time.strftime('%d/%m/%Y %H:%M')}\n"
                                f"🏥 **Template:** {template_info.get('name', 'Padrão')}\n"
                                f"👨‍⚕️ **Especialidade:** {template_info.get('specialty', 'Clínica Geral')}\n\n"
                                f"**Prontuário:**\n\n{prontuario}"
                            )

                            # Split prontuário if too long for Telegram (max 4096 chars)
                            if len(prontuario_text) > 4000:
                                # Send header first
                                header = (
                                    "📋 **PRONTUÁRIO MÉDICO**\n\n"
                                    f"👤 **Paciente:** {patient_data['full_name']}\n"
                                    f"📅 **Data:** {time.strftime('%d/%m/%Y %H:%M')}\n"
                                    f"🏥 **Template:** {template_info.get('name', 'Padrão')}\n"
                                    f"👨‍⚕️ **Especialidade:** {template_info.get('specialty', 'Clínica Geral')}\n\n"
                                )

                                await update.message.reply_text(header, parse_mode='Markdown')

                                # Split prontuário content into chunks
                                prontuario_chunks = [prontuario[i:i+3500] for i in range(0, len(prontuario), 3500)]
                                for i, chunk in enumerate(prontuario_chunks):
                                    part_text = f"**Prontuário (Parte {i+1}/{len(prontuario_chunks)}):**\n\n{chunk}"
                                    await update.message.reply_text(part_text, parse_mode='Markdown')
                            else:
                                await update.message.reply_text(prontuario_text, parse_mode='Markdown')

                        logger.info(f"✅ Audio processed successfully for patient {patient_data['full_name']}")

                    else:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=processing_msg.message_id,
                            text=f"❌ Erro no processamento: {result['error']}"
                        )

                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

        except Exception as error:
            logger.error(f"❌ Error processing audio: {error}")
            await update.message.reply_text("❌ Erro ao processar áudio. Tente novamente.")