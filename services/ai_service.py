"""
AI Service for DocZap Telegram Bot
Handles audio transcription and medical processing
"""

import os
import asyncio
from typing import Dict, Any, Optional
from loguru import logger
import httpx
import aiofiles

class AIService:
    def __init__(self):
        self.ai_processor_url = os.getenv(
            'AI_PROCESSOR_URL',
            'https://saude-ai-processor-production-bebd.up.railway.app'
        )
        self.web_app_url = os.getenv(
            'WEB_APP_URL',
            'https://prontodoc.site'
        )

        # HTTP client for async requests
        self.client = httpx.AsyncClient(timeout=120.0)

        logger.info(f"🤖 AI Service initialized with processor: {self.ai_processor_url}")
        logger.info(f"🌐 Web App URL: {self.web_app_url}")

    async def transcribe_audio(self, audio_file_path: str, doctor_session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio file to text
        Uses the Railway AI processor
        """
        try:
            logger.info("🎙️ Starting audio transcription...")

            # Read audio file
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_data = await audio_file.read()

            # Prepare multipart form data
            files = {
                'audio': ('audio.ogg', audio_data, 'audio/ogg')
            }

            data = {
                'doctor_id': doctor_session['profile_id']
            }

            # Call AI processor transcription endpoint
            response = await self.client.post(
                f"{self.ai_processor_url}/api/doctor/transcribe-audio",
                files=files,
                data=data
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info("✅ Audio transcribed successfully")
                    return {
                        "success": True,
                        "transcription": result.get('transcription'),
                        "duration": result.get('duration')
                    }
                else:
                    logger.error(f"❌ Transcription failed: {result.get('error')}")
                    return {
                        "success": False,
                        "error": result.get('error', 'Transcription failed')
                    }
            else:
                logger.error(f"❌ Transcription request failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Transcription service error: {response.status_code}"
                }

        except Exception as error:
            logger.error(f"❌ Transcription error: {error}")
            return {
                "success": False,
                "error": "Transcription service unavailable"
            }

    async def generate_prontuario(
        self,
        transcription: str,
        patient_data: Dict[str, Any],
        doctor_session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate medical prontuario from transcription
        Uses the Railway AI processor
        """
        try:
            logger.info("📋 Generating medical prontuario...")

            payload = {
                "transcription_text": transcription,
                "patient_data": {
                    "name": patient_data["full_name"],
                    "cpf": patient_data["cpf"],
                    "pin": patient_data["pin"]
                },
                "doctor_id": doctor_session["profile_id"],
                "template_id": template["id"] if template else None
            }

            # Call AI processor prontuario generation endpoint
            response = await self.client.post(
                f"{self.ai_processor_url}/api/doctor/generate-prontuario",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info("✅ Prontuario generated successfully")
                    return {
                        "success": True,
                        "prontuario": result.get('prontuario'),
                        "sections": result.get('sections', {}),
                        "metadata": result.get('metadata', {})
                    }
                else:
                    logger.error(f"❌ Prontuario generation failed: {result.get('error')}")
                    return {
                        "success": False,
                        "error": result.get('error', 'Prontuario generation failed')
                    }
            else:
                logger.error(f"❌ Prontuario generation request failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Prontuario generation service error: {response.status_code}"
                }

        except Exception as error:
            logger.error(f"❌ Prontuario generation error: {error}")
            return {
                "success": False,
                "error": "Prontuario generation service unavailable"
            }

    async def save_prontuario(
        self,
        prontuario_data: Dict[str, Any],
        patient_id: str,
        doctor_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save prontuario to database
        Uses the Railway AI processor
        """
        try:
            logger.info("💾 Saving prontuario to database...")

            payload = {
                "patient_id": patient_id,
                "doctor_id": doctor_session["profile_id"],
                "prontuario_content": prontuario_data["prontuario"],
                "transcription": prontuario_data["transcription"],
                "sections": prontuario_data["sections"],
                "metadata": {
                    **prontuario_data["metadata"],
                    "source": "telegram-bot",
                    "telegram_user_id": doctor_session["telegram_user_id"]
                }
            }

            response = await self.client.post(
                f"{self.ai_processor_url}/api/doctor/save-prontuario",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info("✅ Prontuario saved successfully")
                    return {
                        "success": True,
                        "prontuario_id": result.get('prontuario_id')
                    }
                else:
                    logger.error(f"❌ Prontuario save failed: {result.get('error')}")
                    return {
                        "success": False,
                        "error": result.get('error', 'Save failed')
                    }
            else:
                logger.error(f"❌ Prontuario save request failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Save service error: {response.status_code}"
                }

        except Exception as error:
            logger.error(f"❌ Prontuario save error: {error}")
            return {
                "success": False,
                "error": "Save service unavailable"
            }

    async def process_consultation_direct(
        self,
        audio_file_path: str,
        patient_data: Dict[str, Any],
        doctor_session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process consultation directly with AI processor
        Sends audio file directly to AI processor for transcription + prontuário generation
        """
        try:
            logger.info("🤖 Starting direct AI processor consultation...")

            # Prepare the payload for AI processor
            patient_name = patient_data.get("full_name", "Paciente")
            template_name = template.get("name", "Consulta Geral (SOAP)") if template else "Consulta Geral (SOAP)"
            template_specialty = template.get("specialty", "Clínica Geral") if template else "Clínica Geral"
            ai_prompt_template = template.get("ai_prompt_template") if template else None

            # Read audio file
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_data = await audio_file.read()

            # Prepare multipart form data for direct transcription + prontuário
            files = {
                'audio': ('audio.ogg', audio_data, 'audio/ogg')
            }

            data = {
                'patient_name': patient_name,
                'doctor_id': doctor_session['profile_id'],
                'template_name': template_name,
                'template_specialty': template_specialty,
                'language': 'pt-BR'
            }

            # Only add custom template if it exists and is not a placeholder
            # Placeholder templates like "Template padrão SOAP para consulta geral" should be ignored
            # so the AI processor uses its comprehensive default SOAP prompt
            if ai_prompt_template and ai_prompt_template.strip() and not ai_prompt_template.startswith("Template padrão"):
                logger.info(f"📋 Using custom AI prompt template from database ({len(ai_prompt_template)} chars)")
                data['ai_prompt_template'] = ai_prompt_template
            else:
                logger.info("📋 Using default AI processor SOAP prompt (comprehensive medical instructions)")

            # Call AI processor direct transcription + prontuário endpoint
            response = await self.client.post(
                f"{self.ai_processor_url}/api/doctor/process-direct",
                files=files,
                data=data
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info("✅ Direct AI processing completed successfully")
                    return {
                        "success": True,
                        "transcription": result.get('transcript', ''),
                        "prontuario": result.get('prontuario', ''),
                        "duration": result.get('duration'),
                        "processing_time": result.get('processing_time'),
                        "template": {
                            "name": template_name,
                            "specialty": template_specialty
                        }
                    }
                else:
                    logger.error(f"❌ AI processing failed: {result.get('error')}")
                    return {
                        "success": False,
                        "error": result.get('error', 'AI processing failed')
                    }
            else:
                logger.error(f"❌ AI processor request failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"AI processor error: {response.status_code}"
                }

        except Exception as error:
            logger.error(f"❌ Direct consultation processing error: {error}")
            return {
                "success": False,
                "error": "Direct AI processing failed"
            }

    async def process_consultation(
        self,
        audio_file_path: str,
        patient_data: Dict[str, Any],
        doctor_session: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process complete consultation flow
        Uses direct AI processor integration for Telegram bot
        """
        try:
            # Use direct AI processor method for Telegram bot
            result = await self.process_consultation_direct(
                audio_file_path,
                patient_data,
                doctor_session,
                template
            )

            if result["success"]:
                # Optionally save to database via AI processor or skip for Telegram
                logger.info("🎉 Consultation processed successfully via direct AI processor")

            return result

        except Exception as error:
            logger.error(f"❌ Consultation processing error: {error}")
            return {
                "success": False,
                "error": "Consultation processing failed"
            }

    async def get_templates(self, doctor_session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get available consultation templates for the doctor from web app API
        """
        try:
            logger.info("📋 Fetching consultation templates from web app...")
            logger.info(f"   - Web App URL: {self.web_app_url}")
            logger.info(f"   - Doctor Profile ID: {doctor_session.get('profile_id')}")

            # Use the web app's consultation templates API
            headers = {}

            # Add authentication if we have a session token
            if doctor_session.get('session_token'):
                token = doctor_session.get('session_token')
                headers["Authorization"] = f"Bearer {token}"
                logger.info("🔐 Using authentication token for templates request")
                logger.info(f"   - Token (first 20 chars): {token[:20]}...")
                logger.info(f"   - Token (last 20 chars): ...{token[-20:]}")
            else:
                logger.info("ℹ️ No authentication token, fetching public templates only")

            api_url = f"{self.web_app_url}/api/doctor/consultation-templates"
            logger.info(f"📡 Making GET request to: {api_url}")

            response = await self.client.get(api_url, headers=headers)

            logger.info(f"📡 Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"📡 Response JSON: {result.get('success')}, {result.get('count', 0)} templates")

                if result.get('success'):
                    templates = result.get('templates', [])
                    logger.info(f"✅ Found {len(templates)} templates from web app")

                    # Detailed template breakdown
                    public_count = sum(1 for t in templates if t.get('is_public'))
                    default_count = sum(1 for t in templates if t.get('is_default'))
                    doctor_own_count = sum(1 for t in templates if t.get('created_by') == doctor_session.get('profile_id'))

                    logger.info(f"   - Public templates: {public_count}")
                    logger.info(f"   - Default templates: {default_count}")
                    logger.info(f"   - Doctor's own templates: {doctor_own_count}")

                    # List all templates
                    for i, t in enumerate(templates, 1):
                        logger.info(f"   {i}. {t.get('name')} - created_by: {t.get('created_by')}, public: {t.get('is_public')}, default: {t.get('is_default')}")

                    return {
                        "success": True,
                        "templates": templates
                    }
                else:
                    logger.error(f"❌ Web app template fetch failed: {result.get('error')}")
                    return self._get_fallback_templates()
            else:
                logger.error(f"❌ Web app template request failed: {response.status_code}")
                logger.error(f"Response body: {response.text[:500]}")
                # Return fallback template on error
                return self._get_fallback_templates()

        except Exception as error:
            logger.error(f"❌ Template fetch error: {error}")
            # Return fallback template on error
            return self._get_fallback_templates()

    def _get_fallback_templates(self) -> Dict[str, Any]:
        """Return fallback templates when API is unavailable"""
        fallback_templates = [
            {
                "id": "default-soap",
                "name": "Consulta Geral (SOAP)",
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
                # No ai_prompt_template - let AI processor use its comprehensive default SOAP prompt
                "ai_prompt_template": None,
                "is_default": True,
                "is_public": True
            },
            {
                "id": "cardiology",
                "name": "Cardiologia",
                "specialty": "Cardiologia",
                "template_structure": {
                    "sections": [
                        {"name": "Sintomas Cardiovasculares", "required": True},
                        {"name": "Exame Cardiovascular", "required": True},
                        {"name": "ECG", "required": False},
                        {"name": "Diagnóstico", "required": True},
                        {"name": "Conduta", "required": True}
                    ]
                },
                # No ai_prompt_template - let AI processor use its comprehensive default SOAP prompt
                "ai_prompt_template": None,
                "is_default": False,
                "is_public": True
            },
            {
                "id": "dermatology",
                "name": "Dermatologia",
                "specialty": "Dermatologia",
                "template_structure": {
                    "sections": [
                        {"name": "Lesões Cutâneas", "required": True},
                        {"name": "Exame Dermatológico", "required": True},
                        {"name": "Diagnóstico Dermatológico", "required": True},
                        {"name": "Tratamento", "required": True}
                    ]
                },
                # No ai_prompt_template - let AI processor use its comprehensive default SOAP prompt
                "ai_prompt_template": None,
                "is_default": False,
                "is_public": True
            }
        ]

        return {
            "success": True,
            "templates": fallback_templates,
            "fallback": True
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()