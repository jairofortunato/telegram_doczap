"""
Subscription Service for Telegram/WhatsApp Bot
Handles subscription tier validation and payment link generation
"""

import os
import httpx
from typing import Dict, Any
from loguru import logger


class SubscriptionService:
    def __init__(self):
        self.web_app_url = os.getenv(
            'WEB_APP_URL',
            'https://prontuarioautomatico.vercel.app'
        )
        self.stripe_payment_link = os.getenv(
            'STRIPE_PAYMENT_LINK',
            'https://prontuarioautomatico.vercel.app/pricing'
        )

        # HTTP client for async requests
        self.client = httpx.AsyncClient(timeout=30.0)

        logger.info(f"💳 Subscription Service initialized")
        logger.info(f"🌐 Web App URL: {self.web_app_url}")
        logger.info(f"💰 Payment Link: {self.stripe_payment_link}")

    async def check_consultation_limit(self, user_id: str, doctor_session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if user can create a consultation
        Returns:
            - can_create: bool
            - tier: 'free' or 'professional'
            - consultations_used: int
            - consultations_limit: int
            - upgrade_required: bool
            - message: str
        """
        try:
            logger.info(f"🔍 Checking consultation limit for user {user_id}")

            # Call web app API to check subscription status
            response = await self.client.get(
                f"{self.web_app_url}/api/subscription/status",
                headers={
                    "Authorization": f"Bearer {doctor_session.get('session_token', '')}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                balance = data.get('balance', {})
                subscription = data.get('subscription', {})

                tier = balance.get('tier', 'free')

                # FREE TIER CHECK
                if tier == 'free':
                    consultations_used = balance.get('prontuarios_used', 0)
                    consultations_limit = balance.get('prontuarios_limit', 3)

                    if consultations_used >= consultations_limit:
                        logger.warning(f"❌ User {user_id} exceeded free tier limit ({consultations_used}/{consultations_limit})")
                        return {
                            "can_create": False,
                            "tier": "free",
                            "consultations_used": consultations_used,
                            "consultations_limit": consultations_limit,
                            "upgrade_required": True,
                            "message": f"Limite de consultas gratuitas atingido ({consultations_limit}/{consultations_limit}). Faça upgrade para Professional."
                        }
                    else:
                        remaining = consultations_limit - consultations_used
                        logger.info(f"✅ User {user_id} can create consultation ({consultations_used + 1}/{consultations_limit})")
                        return {
                            "can_create": True,
                            "tier": "free",
                            "consultations_used": consultations_used,
                            "consultations_limit": consultations_limit,
                            "remaining": remaining,
                            "upgrade_required": False,
                            "message": f"Consulta {consultations_used + 1} de {consultations_limit}"
                        }

                # PROFESSIONAL TIER - unlimited
                else:
                    logger.info(f"✅ User {user_id} has Professional tier - unlimited consultations")
                    return {
                        "can_create": True,
                        "tier": "professional",
                        "consultations_used": 0,
                        "consultations_limit": -1,  # -1 means unlimited
                        "upgrade_required": False,
                        "message": "Plano Professional - Consultas ilimitadas"
                    }

            else:
                logger.error(f"❌ Subscription check failed: {response.status_code}")
                # Default to allowing if API fails (graceful degradation)
                return {
                    "can_create": True,
                    "tier": "unknown",
                    "consultations_used": 0,
                    "consultations_limit": 3,
                    "upgrade_required": False,
                    "message": "Verificação de assinatura falhou - permitindo acesso"
                }

        except Exception as e:
            logger.error(f"❌ Error checking consultation limit: {e}")
            # Default to allowing if check fails (graceful degradation)
            return {
                "can_create": True,
                "tier": "unknown",
                "consultations_used": 0,
                "consultations_limit": 3,
                "upgrade_required": False,
                "message": "Erro na verificação - permitindo acesso"
            }

    async def increment_usage(self, user_id: str, doctor_session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Increment usage counter after successful consultation (Free tier only)
        Professional tier doesn't need this as they have unlimited consultations
        """
        try:
            logger.info(f"📊 Incrementing usage for user {user_id}")

            # Call web app API to increment usage
            response = await self.client.post(
                f"{self.web_app_url}/api/subscription/increment-usage",
                headers={
                    "Authorization": f"Bearer {doctor_session.get('session_token', '')}"
                }
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Usage incremented successfully")
                return {
                    "success": True,
                    "consultations_used": result.get('consultations_used', 0)
                }
            else:
                logger.error(f"❌ Failed to increment usage: {response.status_code}")
                return {
                    "success": False,
                    "error": "Failed to update usage"
                }

        except Exception as e:
            logger.error(f"❌ Error incrementing usage: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_payment_link(self, user_id: str) -> str:
        """
        Get Stripe payment link for Professional subscription
        Can include user_id as metadata for tracking
        """
        # For now, return the pricing page URL
        # In production, this could be a Stripe Payment Link with prefilled customer data
        return f"{self.stripe_payment_link}?user_id={user_id}"

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
