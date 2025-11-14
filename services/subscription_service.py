"""
Subscription Service for Telegram/WhatsApp Bot
Handles subscription tier validation and payment link generation
"""

import os
import httpx
import stripe
from typing import Dict, Any
from loguru import logger
from supabase import create_client, Client


class SubscriptionService:
    def __init__(self):
        self.web_app_url = os.getenv(
            'WEB_APP_URL',
            'https://prontodoc.site'
        )
        self.stripe_payment_link = os.getenv(
            'STRIPE_PAYMENT_LINK',
            'https://prontodoc.site/pricing'
        )

        # HTTP client for async requests
        self.client = httpx.AsyncClient(timeout=30.0)

        # Initialize Stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_price_id = os.getenv('STRIPE_PRICE_ID_PRO_MONTHLY')

        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

        logger.info(f"💳 Subscription Service initialized")
        logger.info(f"🌐 Web App URL: {self.web_app_url}")
        logger.info(f"💰 Payment Link: {self.stripe_payment_link}")
        logger.info(f"🔑 Stripe configured: {bool(stripe.api_key)}")
        logger.info(f"🗄️ Supabase configured: {bool(self.supabase)}")

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

    async def check_consultation_limit_direct(self, user_id: str) -> Dict[str, Any]:
        """
        Check consultation limit directly from Supabase profiles table
        This is used by WhatsApp/Telegram bot to avoid calling web app API

        Returns:
            - can_create: bool
            - tier: 'free' or 'professional'
            - consultations_used: int
            - consultations_limit: int
            - upgrade_required: bool
            - message: str
        """
        try:
            if not self.supabase:
                logger.error("❌ Supabase not configured - BLOCKING ACCESS")
                return {
                    "can_create": False,
                    "tier": "unknown",
                    "upgrade_required": True,
                    "message": "Sistema de verificação não configurado. Entre em contato com o suporte."
                }

            logger.info(f"🔍 Checking consultation limit directly for user {user_id}")

            # Check if user has professional subscription
            subscription_response = self.supabase.from_('subscriptions') \
                .select('tier, status') \
                .eq('user_id', user_id) \
                .eq('status', 'active') \
                .execute()

            if subscription_response.data and len(subscription_response.data) > 0:
                subscription = subscription_response.data[0]
                if subscription.get('tier') == 'professional':
                    logger.info(f"✅ User {user_id} has Professional tier - unlimited consultations")
                    return {
                        "can_create": True,
                        "tier": "professional",
                        "consultations_used": 0,
                        "consultations_limit": -1,
                        "upgrade_required": False,
                        "message": "Plano Professional - Consultas ilimitadas"
                    }

            # User is on free tier - check profile
            profile_response = self.supabase.from_('profiles') \
                .select('free_consultations_used, free_consultations_limit') \
                .eq('user_id', user_id) \
                .execute()

            if not profile_response.data or len(profile_response.data) == 0:
                logger.warning(f"⚠️ Profile not found for user {user_id}")
                return {
                    "can_create": True,
                    "tier": "free",
                    "consultations_used": 0,
                    "consultations_limit": 5,
                    "upgrade_required": False,
                    "message": "Profile not found - allowing access"
                }

            profile = profile_response.data[0]
            consultations_used = profile.get('free_consultations_used', 0)
            consultations_limit = profile.get('free_consultations_limit', 5)

            # Check if limit reached
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

            # User can create consultation
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

        except Exception as e:
            logger.error(f"❌ Error checking consultation limit: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # STRICT MODE - block access if check fails to prevent payment bypass
            return {
                "can_create": False,
                "tier": "unknown",
                "consultations_used": 0,
                "consultations_limit": 5,
                "upgrade_required": True,
                "message": "Erro na verificação de assinatura. Tente novamente ou entre em contato com o suporte."
            }

    async def create_checkout_session(self, user_id: str, user_email: str, user_phone: str = None) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for Professional subscription

        Args:
            user_id: User ID to store in metadata
            user_email: User email for Stripe customer
            user_phone: Optional phone number

        Returns:
            - success: bool
            - checkout_url: str (if successful)
            - error: str (if failed)
        """
        try:
            if not stripe.api_key or not self.stripe_price_id:
                logger.error("❌ Stripe not configured")
                return {
                    "success": False,
                    "error": "Payment system not configured"
                }

            logger.info(f"💳 Creating checkout session for user {user_id}")

            # Get or create Stripe customer
            customer = await self._get_or_create_customer(user_id, user_email, user_phone)

            if not customer:
                return {
                    "success": False,
                    "error": "Failed to create customer"
                }

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{self.web_app_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.web_app_url}/payment/cancel",
                metadata={
                    'user_id': user_id,
                    'source': 'whatsapp_bot'
                },
                subscription_data={
                    'metadata': {
                        'user_id': user_id,
                        'source': 'whatsapp_bot'
                    }
                }
            )

            logger.info(f"✅ Checkout session created: {session.id}")
            return {
                "success": True,
                "checkout_url": session.url,
                "session_id": session.id
            }

        except Exception as e:
            logger.error(f"❌ Error creating checkout session: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_or_create_customer(self, user_id: str, user_email: str, user_phone: str = None) -> stripe.Customer:
        """
        Get existing Stripe customer or create a new one

        Args:
            user_id: User ID to search/store in metadata
            user_email: User email
            user_phone: Optional phone number

        Returns:
            Stripe Customer object or None
        """
        try:
            # Search for existing customer by metadata
            customers = stripe.Customer.list(
                email=user_email,
                limit=1
            )

            if customers.data:
                customer = customers.data[0]
                logger.info(f"✅ Found existing Stripe customer: {customer.id}")
                return customer

            # Create new customer
            customer_data = {
                'email': user_email,
                'metadata': {
                    'user_id': user_id,
                    'source': 'whatsapp_bot'
                }
            }

            if user_phone:
                customer_data['phone'] = user_phone

            customer = stripe.Customer.create(**customer_data)
            logger.info(f"✅ Created new Stripe customer: {customer.id}")
            return customer

        except Exception as e:
            logger.error(f"❌ Error getting/creating customer: {e}")
            return None

    async def increment_usage_direct(self, user_id: str) -> Dict[str, Any]:
        """
        Increment usage counter directly in Supabase (Free tier only)
        Professional tier doesn't need this as they have unlimited consultations
        """
        try:
            if not self.supabase:
                logger.error("❌ Supabase not configured")
                return {
                    "success": False,
                    "error": "Database not configured"
                }

            logger.info(f"📊 Incrementing usage directly for user {user_id}")

            # Get current count
            profile_response = self.supabase.from_('profiles') \
                .select('free_consultations_used') \
                .eq('user_id', user_id) \
                .execute()

            if not profile_response.data or len(profile_response.data) == 0:
                logger.error(f"❌ Profile not found for user {user_id}")
                return {
                    "success": False,
                    "error": "Profile not found"
                }

            current_count = profile_response.data[0].get('free_consultations_used', 0)
            new_count = current_count + 1

            # Update count
            update_response = self.supabase.from_('profiles') \
                .update({'free_consultations_used': new_count}) \
                .eq('user_id', user_id) \
                .execute()

            logger.info(f"✅ Usage incremented to {new_count}")
            return {
                "success": True,
                "consultations_used": new_count
            }

        except Exception as e:
            logger.error(f"❌ Error incrementing usage: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
