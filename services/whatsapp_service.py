"""
WhatsApp Service for DOCZAP
Handles WhatsApp Business API communication
"""

import os
import httpx
import tempfile
from typing import Dict, Any, Optional, List
from loguru import logger
from utils.url_utils import build_graph_api_url, clean_string, clean_phone_number, clean_message_id

class WhatsAppService:
    def __init__(self):
        # Clean environment variables to remove any invisible characters
        self.access_token = clean_string(os.getenv('WHATSAPP_ACCESS_TOKEN', ''))
        self.phone_number_id = clean_string(os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''))
        self.api_version = clean_string(os.getenv('WHATSAPP_API_VERSION', 'v18.0'))

        # No longer need base_url as we'll build URLs dynamically

        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp credentials not configured - WhatsApp functionality disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("📱 WhatsApp Service initialized")

        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """Send text message to WhatsApp user"""
        if not self.enabled:
            return {"success": False, "error": "WhatsApp not configured"}

        try:
            # Build clean URL
            url = build_graph_api_url(self.api_version, self.phone_number_id, "messages")
            logger.debug(f"WhatsApp send_text URL: {repr(url)}")

            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone_number(to),
                "type": "text",
                "text": {"body": text}
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            response = await self.client.post(url, json=payload, headers=headers)
            result = response.json()

            if response.status_code == 200:
                logger.info(f"✅ WhatsApp message sent to {to}")
                return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            else:
                logger.error(f"❌ Failed to send WhatsApp message: {result}")
                return {"success": False, "error": result}

        except Exception as e:
            logger.error(f"Error sending WhatsApp text message: {e}")
            return {"success": False, "error": str(e)}

    async def send_interactive_message(self, to: str, header_text: str,
                                     body_text: str, footer_text: str,
                                     buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """Send interactive message with buttons"""
        if not self.enabled:
            return {"success": False, "error": "WhatsApp not configured"}

        try:
            # Build clean URL
            url = build_graph_api_url(self.api_version, self.phone_number_id, "messages")
            logger.debug(f"WhatsApp send_interactive URL: {repr(url)}")

            # Build button components (max 3 buttons)
            button_components = []
            for i, button in enumerate(buttons[:3]):
                button_components.append({
                    "type": "reply",
                    "reply": {
                        "id": button.get("id", f"btn_{i}"),
                        "title": button.get("title", f"Option {i+1}")
                    }
                })

            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone_number(to),
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {"type": "text", "text": header_text},
                    "body": {"text": body_text},
                    "footer": {"text": footer_text},
                    "action": {"buttons": button_components}
                }
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            response = await self.client.post(url, json=payload, headers=headers)
            result = response.json()

            if response.status_code == 200:
                logger.info(f"✅ WhatsApp interactive message sent to {to}")
                return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            else:
                logger.error(f"❌ Failed to send WhatsApp interactive message: {result}")
                return {"success": False, "error": result}

        except Exception as e:
            logger.error(f"Error sending WhatsApp interactive message: {e}")
            return {"success": False, "error": str(e)}

    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download media from WhatsApp"""
        if not self.enabled:
            return None

        try:
            # First, get media URL - build clean URL for media endpoint
            url = build_graph_api_url(self.api_version, clean_message_id(media_id), "")
            logger.debug(f"WhatsApp download_media URL: {repr(url)}")
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.client.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"Failed to get WhatsApp media URL: {response.json()}")
                return None

            media_info = response.json()
            media_url = media_info.get('url')

            if not media_url:
                logger.error("No media URL in WhatsApp response")
                return None

            # Download actual media
            media_response = await self.client.get(media_url, headers=headers)

            if media_response.status_code == 200:
                logger.info(f"✅ WhatsApp media downloaded: {media_id}")
                return media_response.content
            else:
                logger.error(f"Failed to download WhatsApp media: {media_response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error downloading WhatsApp media: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark WhatsApp message as read"""
        if not self.enabled:
            return {"success": False, "error": "WhatsApp not configured"}

        try:
            # Build clean URL
            url = build_graph_api_url(self.api_version, self.phone_number_id, "messages")
            logger.debug(f"WhatsApp mark_as_read URL: {repr(url)}")

            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": clean_message_id(message_id)
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            response = await self.client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": response.json()}

        except Exception as e:
            logger.error(f"Error marking WhatsApp message as read: {e}")
            return {"success": False, "error": str(e)}