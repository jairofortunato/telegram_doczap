"""
Telegram utility functions for webhook-based bot
"""

import requests
from loguru import logger
from typing import Optional, Dict, Any

def send_telegram_message(bot_token: str, chat_id: int, text: str) -> bool:
    """Send a message to Telegram chat"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        return response.json().get("ok", False)

    except Exception as e:
        logger.error(f"Failed to send telegram message: {e}")
        return False

def get_file_info(bot_token: str, file_id: str) -> Optional[Dict[str, Any]]:
    """Get file information from Telegram"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getFile"
        params = {"file_id": file_id}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        if data.get("ok") and "result" in data:
            file_path = data["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

            return {
                "file_path": file_path,
                "download_url": download_url,
                "file_size": data["result"].get("file_size", 0)
            }

        return None

    except Exception as e:
        logger.error(f"Failed to get file info: {e}")
        return None

def download_telegram_file(download_url: str, local_path: str) -> bool:
    """Download file from Telegram servers"""
    try:
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Successfully downloaded file to {local_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return False

def chunk_text(text: str, max_length: int = 4096) -> list[str]:
    """Split text into chunks that fit in Telegram messages"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = line + '\n'
            else:
                # Line is too long, split it
                while len(line) > max_length:
                    chunks.append(line[:max_length])
                    line = line[max_length:]
                current_chunk = line + '\n'

    if current_chunk:
        chunks.append(current_chunk.rstrip())

    return chunks

def format_error_message(error_type: str, error_message: str, error_code: str = None, details: dict = None, suggestions: list = None) -> str:
    """Format detailed error message for Telegram"""

    # Error type icons
    icons = {
        "auth": "🔐",
        "network": "🌐",
        "ai_processing": "🤖",
        "file_processing": "📁",
        "template": "📋",
        "validation": "⚠️",
        "system": "⚙️"
    }

    icon = icons.get(error_type, "❌")

    error_msg = f"{icon} *Erro {error_type.title()}*\n\n"
    error_msg += f"💬 *Mensagem:* {error_message}\n"

    if error_code:
        error_msg += f"🔢 *Código:* `{error_code}`\n"

    if details:
        error_msg += f"\n📋 *Detalhes:*\n"
        for key, value in details.items():
            if value:  # Only show non-empty values
                key_formatted = key.replace('_', ' ').title()
                error_msg += f"• {key_formatted}: `{value}`\n"

    if suggestions:
        error_msg += f"\n💡 *Sugestões:*\n"
        for suggestion in suggestions:
            error_msg += f"• {suggestion}\n"

    error_msg += f"\n🆘 Se o problema persistir, entre em contato com o suporte técnico."

    return error_msg

def send_error_message(bot_token: str, chat_id: int, error_type: str, error_message: str,
                      error_code: str = None, details: dict = None, suggestions: list = None) -> bool:
    """Send formatted error message to Telegram chat"""
    formatted_error = format_error_message(error_type, error_message, error_code, details, suggestions)
    return send_telegram_message(bot_token, chat_id, formatted_error)