"""
Image Processing Service for DocZap
Uses OpenAI Vision to extract text/information from medical images
and integrates content into existing prontuários
"""

import os
import base64
from typing import Dict, Any, Optional
from loguru import logger
import openai
from supabase import create_client, Client


class ImageProcessingService:
    def __init__(self):
        """Initialize image processing service with OpenAI and Supabase"""
        # OpenAI client
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        self.model = "gpt-4o"  # gpt-4o supports vision

        # Supabase client for database operations
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        logger.info("📸 Image Processing Service initialized")

    async def extract_text_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract text and medical information from an image using OpenAI Vision

        Args:
            image_data: Raw image bytes

        Returns:
            Dict with success status and extracted content
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # Prepare messages for OpenAI Vision
            messages = [
                {
                    "role": "system",
                    "content": """Você é um assistente médico especializado em extrair informações de imagens médicas.

Analise a imagem e extraia TODAS as informações médicas relevantes, incluindo:
- Resultados de exames (valores, unidades, referências)
- Prescrições médicas (medicamentos, dosagens, frequência)
- Diagnósticos e CIDs
- Sinais vitais
- Anotações médicas
- Datas e informações do paciente

Formate a resposta de forma estruturada e clara em português brasileiro."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Por favor, extraia todas as informações médicas desta imagem de forma detalhada e estruturada:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"  # High detail for medical images
                            }
                        }
                    ]
                }
            ]

            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                timeout=60
            )

            extracted_text = response.choices[0].message.content

            if not extracted_text:
                return {
                    "success": False,
                    "error": "Nenhum texto extraído da imagem"
                }

            logger.info(f"✅ Text extracted from image successfully ({len(extracted_text)} chars)")

            return {
                "success": True,
                "extracted_text": extracted_text,
                "tokens_used": response.usage.total_tokens if response.usage else None
            }

        except Exception as e:
            logger.error(f"❌ Error extracting text from image: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar imagem: {str(e)}"
            }

    async def get_last_prontuario(self, doctor_session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the last prontuário created by this doctor

        Args:
            doctor_session: Doctor session with profile_id

        Returns:
            Last prontuário or None
        """
        try:
            profile_id = doctor_session.get("profile_id")
            if not profile_id:
                logger.error("No profile_id in doctor session")
                return None

            # Get last prontuário created by this doctor from prontuarios table
            result = self.supabase.table('prontuarios').select(
                '*'
            ).eq('created_by', profile_id).order(
                'created_at', desc=True
            ).limit(1).execute()

            if result.data and len(result.data) > 0:
                prontuario = result.data[0]
                logger.info(f"✅ Found last prontuário: {prontuario.get('id')}")
                return prontuario
            else:
                logger.warning("No prontuário found for this doctor")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting last prontuário: {e}")
            return None

    async def merge_image_content_into_prontuario(
        self,
        prontuario: Dict[str, Any],
        extracted_content: str
    ) -> Dict[str, Any]:
        """
        Use AI to intelligently merge extracted image content into existing prontuário

        Args:
            prontuario: Existing prontuário data (from prontuarios table)
            extracted_content: Text extracted from image

        Returns:
            Updated prontuário content
        """
        try:
            # Get current prontuário content (stored as text in 'content' field)
            current_content = prontuario.get('content', '')

            # Prepare prompt for AI to merge content
            merge_prompt = f"""Você é um assistente médico especializado em integrar informações de exames e documentos médicos em prontuários.

**PRONTUÁRIO ATUAL:**
{current_content or '(vazio)'}

---

**INFORMAÇÕES EXTRAÍDAS DA IMAGEM:**
{extracted_content}

---

**TAREFA:**
Integre de forma inteligente as informações da imagem no prontuário existente.
- Se forem resultados de exames, adicione uma seção "RESULTADOS DE EXAMES" ou adicione à seção Objetivo
- Se forem prescrições/medicamentos, adicione à seção de Plano Terapêutico
- Se forem diagnósticos, adicione à seção de Avaliação
- Mantenha TODA a estrutura e conteúdo existente
- ADICIONE as novas informações de forma organizada e clara
- Use formatação com marcadores, seções e destaques
- Destaque valores de exames com unidades e referências
- Mantenha o formato SOAP se o prontuário já estiver nesse formato

Retorne o prontuário completo atualizado como texto formatado em markdown."""

            messages = [
                {"role": "system", "content": "Você é um assistente médico especializado em prontuários."},
                {"role": "user", "content": merge_prompt}
            ]

            # Call OpenAI to merge content
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=3000,
                timeout=60
            )

            updated_content = response.choices[0].message.content

            if not updated_content:
                return {
                    "success": False,
                    "error": "Failed to merge content"
                }

            logger.info("✅ Successfully merged image content into prontuário")

            return {
                "success": True,
                "updated_content": updated_content
            }

        except Exception as e:
            logger.error(f"❌ Error merging content: {e}")
            return {
                "success": False,
                "error": f"Erro ao integrar conteúdo: {str(e)}"
            }

    async def update_prontuario_in_database(
        self,
        prontuario_id: str,
        updated_content: str
    ) -> Dict[str, Any]:
        """
        Update prontuário in database with merged content

        Args:
            prontuario_id: Prontuário ID to update
            updated_content: Updated prontuário content (text)

        Returns:
            Result of update operation
        """
        try:
            from datetime import datetime

            # Update prontuario in database
            result = self.supabase.table('prontuarios').update({
                'content': updated_content,
                'updated_at': datetime.now().isoformat()
            }).eq('id', prontuario_id).execute()

            if result.data:
                logger.info(f"✅ Updated prontuário {prontuario_id} in database")
                return {
                    "success": True,
                    "prontuario_id": prontuario_id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update database"
                }

        except Exception as e:
            logger.error(f"❌ Error updating database: {e}")
            return {
                "success": False,
                "error": f"Erro ao atualizar banco de dados: {str(e)}"
            }

    async def process_image_and_update_prontuario(
        self,
        image_data: bytes,
        doctor_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete flow: extract text from image and merge into last prontuário

        Args:
            image_data: Raw image bytes
            doctor_session: Doctor session data

        Returns:
            Result of entire operation
        """
        try:
            # Step 1: Extract text from image
            extraction_result = await self.extract_text_from_image(image_data)
            if not extraction_result.get("success"):
                return extraction_result

            extracted_text = extraction_result["extracted_text"]

            # Step 2: Get last prontuário
            last_prontuario = await self.get_last_prontuario(doctor_session)
            if not last_prontuario:
                return {
                    "success": False,
                    "error": "Nenhum prontuário encontrado. Crie um prontuário primeiro enviando um áudio."
                }

            prontuario_id = last_prontuario.get('id')

            # Step 3: Merge content
            merge_result = await self.merge_image_content_into_prontuario(
                last_prontuario,
                extracted_text
            )

            if not merge_result.get("success"):
                return merge_result

            updated_content = merge_result["updated_content"]

            # Step 4: Update database
            update_result = await self.update_prontuario_in_database(
                prontuario_id,
                updated_content
            )

            if not update_result.get("success"):
                return update_result

            # Success!
            return {
                "success": True,
                "message": "Imagem processada e prontuário atualizado com sucesso!",
                "prontuario_id": prontuario_id,
                "extracted_text": extracted_text,
                "updated_content": updated_content
            }

        except Exception as e:
            logger.error(f"❌ Error in complete image processing flow: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar imagem: {str(e)}"
            }
