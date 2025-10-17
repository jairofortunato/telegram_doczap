"""
Consultation Session Manager for DocZap
Manages in-memory consultation sessions with accumulated audio transcripts and image extracts
"""

import time
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime, timedelta


class ConsultationSession:
    """Represents an active consultation session"""

    def __init__(self, phone_number: str, doctor_session: Dict[str, Any]):
        self.phone_number = phone_number
        self.doctor_id = doctor_session.get("profile_id")
        self.doctor_session = doctor_session

        # Accumulated content
        self.audio_transcripts: List[Dict[str, Any]] = []
        self.image_extractions: List[Dict[str, Any]] = []

        # Session metadata
        self.patient_name: Optional[str] = None
        self.template_name: str = "SOAP padrão (Clínica Geral)"
        self.template_specialty: str = "Clínica Geral"
        self.template: Optional[Dict[str, Any]] = None

        # Last generated prontuário
        self.last_prontuario: Optional[str] = None
        self.last_prontuario_timestamp: Optional[datetime] = None

        # Session timing
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        logger.info(f"📋 New consultation session created for {phone_number}")

    def add_audio_transcript(self, transcript: str, duration: float, metadata: Dict[str, Any] = None):
        """Add audio transcript to session"""
        self.audio_transcripts.append({
            "transcript": transcript,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self.last_activity = datetime.now()
        logger.info(f"➕ Added audio transcript ({len(transcript)} chars) - Total: {len(self.audio_transcripts)}")

    def add_image_extraction(self, extracted_text: str, metadata: Dict[str, Any] = None):
        """Add image extraction to session"""
        self.image_extractions.append({
            "extracted_text": extracted_text,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self.last_activity = datetime.now()
        logger.info(f"➕ Added image extraction ({len(extracted_text)} chars) - Total: {len(self.image_extractions)}")

    def get_accumulated_content(self) -> str:
        """Get all accumulated content formatted for prontuário generation"""
        sections = []

        # Add audio transcripts
        if self.audio_transcripts:
            sections.append("=== TRANSCRIÇÕES DE ÁUDIO ===\n")
            for idx, audio in enumerate(self.audio_transcripts, 1):
                sections.append(f"[Áudio {idx}] ({audio['duration']:.1f}s)")
                sections.append(audio['transcript'])
                sections.append("")

        # Add image extractions
        if self.image_extractions:
            sections.append("=== INFORMAÇÕES EXTRAÍDAS DE IMAGENS ===\n")
            for idx, image in enumerate(self.image_extractions, 1):
                sections.append(f"[Imagem {idx}] (Exame/Documento Médico)")
                sections.append(image['extracted_text'])
                sections.append("")

        return "\n".join(sections)

    def set_prontuario(self, prontuario: str):
        """Store the last generated prontuário"""
        self.last_prontuario = prontuario
        self.last_prontuario_timestamp = datetime.now()
        logger.info(f"💾 Prontuário stored in session ({len(prontuario)} chars)")

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired due to inactivity"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return {
            "phone_number": self.phone_number,
            "doctor_id": self.doctor_id,
            "patient_name": self.patient_name,
            "template": self.template_name,
            "audio_count": len(self.audio_transcripts),
            "image_count": len(self.image_extractions),
            "has_prontuario": self.last_prontuario is not None,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "duration_minutes": (datetime.now() - self.created_at).total_seconds() / 60
        }


class ConsultationSessionManager:
    """Manages active consultation sessions in memory"""

    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions: Dict[str, ConsultationSession] = {}
        self.session_timeout_minutes = session_timeout_minutes
        logger.info(f"🗂️ ConsultationSessionManager initialized (timeout: {session_timeout_minutes}m)")

    def get_or_create_session(
        self,
        phone_number: str,
        doctor_session: Dict[str, Any]
    ) -> ConsultationSession:
        """Get existing session or create new one"""

        # Clean expired sessions
        self._cleanup_expired_sessions()

        # Get existing session
        if phone_number in self.sessions:
            session = self.sessions[phone_number]
            logger.info(f"♻️ Using existing session for {phone_number}")
            return session

        # Create new session
        session = ConsultationSession(phone_number, doctor_session)
        self.sessions[phone_number] = session
        logger.info(f"✨ Created new session for {phone_number}")

        return session

    def get_session(self, phone_number: str) -> Optional[ConsultationSession]:
        """Get existing session without creating"""
        return self.sessions.get(phone_number)

    def end_session(self, phone_number: str) -> Optional[ConsultationSession]:
        """End and remove session, returning it for final processing"""
        session = self.sessions.pop(phone_number, None)
        if session:
            logger.info(f"🏁 Ended session for {phone_number}")
            logger.info(f"   📊 Summary: {session.get_summary()}")
        return session

    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired = [
            phone for phone, session in self.sessions.items()
            if session.is_expired(self.session_timeout_minutes)
        ]

        for phone in expired:
            session = self.sessions.pop(phone)
            logger.warning(f"🧹 Cleaned up expired session for {phone}")
            logger.info(f"   📊 Final summary: {session.get_summary()}")

    def get_all_sessions_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all active sessions"""
        return [session.get_summary() for session in self.sessions.values()]

    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)


# Global session manager instance
_session_manager: Optional[ConsultationSessionManager] = None


def get_session_manager(timeout_minutes: int = 30) -> ConsultationSessionManager:
    """Get or create global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = ConsultationSessionManager(session_timeout_minutes=timeout_minutes)
    return _session_manager
