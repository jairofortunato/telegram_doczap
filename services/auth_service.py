"""
Authentication Service for DocZap Telegram Bot
Handles doctor authentication via Telegram
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from loguru import logger
from supabase import create_client, Client

class AuthService:
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Store active doctor sessions
        self.active_sessions: Dict[int, Dict[str, Any]] = {}

        # Store pending login states (email waiting for password)
        self.pending_logins: Dict[int, Dict[str, Any]] = {}

        logger.info("🔐 Auth service initialized")

    async def authenticate_doctor(self, telegram_user_id: int, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate doctor by email and password
        Associates Telegram user with doctor profile
        """
        try:
            logger.info(f"🔐 Authenticating doctor: {email} for Telegram user: {telegram_user_id}")

            # Sign in with Supabase Auth
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                return {"success": False, "error": "Invalid credentials"}

            user = auth_response.user

            # Get doctor profile
            profile_response = self.supabase.table('profiles').select(
                'profile_id, full_name, email, role'
            ).eq('user_id', user.id).eq('role', 'doctor').single().execute()

            if not profile_response.data:
                logger.error("❌ Doctor profile not found")
                return {"success": False, "error": "Doctor profile not found"}

            profile = profile_response.data

            # Store session
            doctor_session = {
                "telegram_user_id": telegram_user_id,
                "user_id": user.id,
                "profile_id": profile["profile_id"],
                "full_name": profile["full_name"],
                "email": profile["email"],
                "role": profile["role"],
                "authenticated_at": datetime.now(),
                "session_token": auth_response.session.access_token if auth_response.session else None,
                "selected_template": None  # For template selection
            }

            self.active_sessions[telegram_user_id] = doctor_session

            logger.info(f"✅ Doctor authenticated: Dr. {profile['full_name']}")
            return {
                "success": True,
                "doctor": doctor_session
            }

        except Exception as error:
            logger.error(f"❌ Authentication error: {error}")
            return {"success": False, "error": "Authentication failed"}

    def get_doctor_session(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get active doctor session"""
        return self.active_sessions.get(telegram_user_id)

    def is_authenticated(self, telegram_user_id: int) -> bool:
        """Check if user is authenticated doctor"""
        session = self.get_doctor_session(telegram_user_id)
        if not session:
            return False

        # Check if session is not older than 7 days (1 week)
        now = datetime.now()
        session_age = now - session["authenticated_at"]
        max_age = timedelta(days=7)  # Changed from 24 hours to 1 week

        if session_age > max_age:
            self.logout(telegram_user_id)
            return False

        return True

    def logout(self, telegram_user_id: int) -> None:
        """Logout doctor"""
        if telegram_user_id in self.active_sessions:
            del self.active_sessions[telegram_user_id]
            logger.info(f"🔓 Doctor logged out: Telegram user {telegram_user_id}")

    def get_active_sessions(self) -> list:
        """Get all active sessions (for admin purposes)"""
        return list(self.active_sessions.values())

    async def search_patient_by_pin(self, pin: str, doctor_session: Dict[str, Any]) -> Dict[str, Any]:
        """Search patient by PIN (same as web app)"""
        try:
            logger.info(f"🔍 Searching patient by PIN: {pin}")

            # Search for patient profile
            patient_response = self.supabase.table('profiles').select(
                'profile_id, full_name, cpf, pin, email, birth_date'
            ).eq('pin', pin).eq('role', 'patient').single().execute()

            if not patient_response.data:
                return {"success": False, "error": "Patient not found"}

            patient = patient_response.data

            # Get patient medical data in parallel
            patient_id = patient["profile_id"]

            # Execute all queries concurrently
            medical_queries = [
                self.supabase.table('medications').select('*').eq('patient_id', patient_id).execute(),
                self.supabase.table('allergies').select('*').eq('patient_id', patient_id).execute(),
                self.supabase.table('exams').select('*').eq('patient_id', patient_id).execute(),
                self.supabase.table('diseases').select('*').eq('patient_id', patient_id).execute(),
                self.supabase.table('consultations').select('*').eq('patient_id', patient_id).execute()
            ]

            # Wait for all queries to complete
            results = await asyncio.gather(*[
                asyncio.create_task(asyncio.to_thread(lambda q=query: q))
                for query in medical_queries
            ], return_exceptions=True)

            medical_data = {
                "medications": results[0].data if not isinstance(results[0], Exception) else [],
                "allergies": results[1].data if not isinstance(results[1], Exception) else [],
                "exams": results[2].data if not isinstance(results[2], Exception) else [],
                "diseases": results[3].data if not isinstance(results[3], Exception) else [],
                "consultations": results[4].data if not isinstance(results[4], Exception) else []
            }

            logger.info(f"✅ Patient found: {patient['full_name']}")
            return {
                "success": True,
                "patient": patient,
                "medical_data": medical_data
            }

        except Exception as error:
            logger.error(f"❌ Patient search error: {error}")
            return {"success": False, "error": "Search failed"}

    def set_selected_template(self, telegram_user_id: int, template: Dict[str, Any]) -> None:
        """Set selected template for doctor session"""
        if telegram_user_id in self.active_sessions:
            self.active_sessions[telegram_user_id]["selected_template"] = template
            logger.info(f"🎯 Template selected for user {telegram_user_id}: {template.get('name', 'Unknown')}")

    def get_selected_template(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get selected template for doctor session"""
        session = self.get_doctor_session(telegram_user_id)
        return session.get("selected_template") if session else None

    def clear_selected_template(self, telegram_user_id: int) -> None:
        """Clear selected template for doctor session"""
        if telegram_user_id in self.active_sessions:
            self.active_sessions[telegram_user_id]["selected_template"] = None
            logger.info(f"🗑️ Template cleared for user {telegram_user_id}")

    def start_login(self, telegram_user_id: int, email: str) -> None:
        """Start login flow - store email and wait for password"""
        self.pending_logins[telegram_user_id] = {
            "email": email,
            "started_at": datetime.now()
        }
        logger.info(f"🔐 Login started for {telegram_user_id} with email {email}")

    def get_pending_login(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get pending login state"""
        pending = self.pending_logins.get(telegram_user_id)
        if pending:
            # Check if login state is not older than 5 minutes
            now = datetime.now()
            age = now - pending["started_at"]
            if age > timedelta(minutes=5):
                # Expired, clear it
                del self.pending_logins[telegram_user_id]
                return None
        return pending

    def clear_pending_login(self, telegram_user_id: int) -> None:
        """Clear pending login state"""
        if telegram_user_id in self.pending_logins:
            del self.pending_logins[telegram_user_id]
            logger.info(f"🗑️ Pending login cleared for {telegram_user_id}")