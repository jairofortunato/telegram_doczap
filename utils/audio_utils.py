"""
Audio utility functions for DocZap Telegram Bot
Handles audio file processing and conversion
"""

import os
import tempfile
from typing import Optional
from loguru import logger
import subprocess

def get_audio_duration(file_path: str) -> float:
    """
    Get audio file duration in seconds using ffmpeg
    """
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            logger.warning("⚠️ Could not get audio duration, returning default")
            return 10.0  # Default duration
    except Exception as error:
        logger.error(f"❌ Error getting audio duration: {error}")
        return 10.0  # Default duration

def convert_audio_to_wav(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert audio file to WAV format using ffmpeg
    Returns the path to the converted file
    """
    try:
        if output_path is None:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name

        # Convert using ffmpeg
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ar', '16000', '-ac', '1',  # 16kHz, mono
            output_path, '-y'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Audio converted to WAV: {output_path}")
            return output_path
        else:
            logger.error(f"❌ FFmpeg conversion failed: {result.stderr}")
            return input_path  # Return original if conversion fails

    except Exception as error:
        logger.error(f"❌ Error converting audio to WAV: {error}")
        return input_path  # Return original if conversion fails

def convert_to_ogg(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert audio file to OGG format using ffmpeg
    Returns the path to the converted file
    """
    try:
        if output_path is None:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                output_path = temp_file.name

        # Convert using ffmpeg
        cmd = ['ffmpeg', '-i', input_path, '-c:a', 'libvorbis', output_path, '-y']

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Audio converted to OGG: {output_path}")
            return output_path
        else:
            logger.error(f"❌ FFmpeg conversion failed: {result.stderr}")
            return input_path

    except Exception as error:
        logger.error(f"❌ Error converting audio to OGG: {error}")
        return input_path

def normalize_audio_volume(input_path: str, target_dBFS: float = -20.0) -> str:
    """
    Normalize audio volume using ffmpeg
    Returns path to normalized audio file
    """
    try:
        # Create temp file for normalized audio
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            normalized_path = temp_file.name

        # Apply volume normalization using ffmpeg
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', 'loudnorm',
            '-c:a', 'libvorbis',
            normalized_path, '-y'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Audio normalized: {normalized_path}")
            return normalized_path
        else:
            logger.warning(f"⚠️ Audio normalization failed: {result.stderr}")
            return input_path

    except Exception as error:
        logger.error(f"❌ Error normalizing audio: {error}")
        return input_path

def reduce_audio_noise(input_path: str) -> str:
    """
    Apply basic noise reduction to improve transcription quality
    Uses ffmpeg if available, otherwise returns original
    """
    try:
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ ffmpeg not available, skipping noise reduction")
            return input_path

        # Create temp file for processed audio
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            output_path = temp_file.name

        # Apply noise reduction using ffmpeg
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', 'highpass=f=200,lowpass=f=3000,volume=2.0',
            '-c:a', 'libvorbis', '-q:a', '4',
            output_path, '-y'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"✅ Noise reduction applied: {output_path}")
            return output_path
        else:
            logger.warning(f"⚠️ Noise reduction failed: {result.stderr}")
            return input_path

    except Exception as error:
        logger.error(f"❌ Error applying noise reduction: {error}")
        return input_path

def validate_audio_file(file_path: str) -> bool:
    """
    Validate if file is a valid audio file
    """
    try:
        duration = get_audio_duration(file_path)

        if duration < 0.5:
            logger.warning("⚠️ Audio too short (< 0.5s)")
            return False

        if duration > 600:  # 10 minutes
            logger.warning("⚠️ Audio too long (> 10 minutes)")
            return False

        return True

    except Exception as error:
        logger.error(f"❌ Invalid audio file: {error}")
        return False

def get_audio_info(file_path: str) -> dict:
    """
    Get basic audio file information
    """
    try:
        duration = get_audio_duration(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        return {
            "duration_seconds": duration,
            "file_size_mb": file_size_mb,
            "format": "ogg" if file_path.endswith('.ogg') else "unknown"
        }

    except Exception as error:
        logger.error(f"❌ Error getting audio info: {error}")
        return {}

def cleanup_temp_files(file_paths: list) -> None:
    """
    Clean up temporary audio files
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"🗑️ Cleaned up temp file: {file_path}")
        except Exception as error:
            logger.warning(f"⚠️ Failed to cleanup {file_path}: {error}")

def process_audio_for_transcription(input_path: str) -> str:
    """
    Complete audio processing pipeline for optimal transcription
    Returns path to processed audio file
    """
    try:
        logger.info("🎵 Starting audio processing pipeline...")

        # Step 1: Validate audio
        if not validate_audio_file(input_path):
            raise ValueError("Invalid audio file")

        # Step 2: Normalize volume
        normalized_path = normalize_audio_volume(input_path)

        # Step 3: Apply noise reduction (if ffmpeg available)
        final_path = reduce_audio_noise(normalized_path)

        # Clean up intermediate file if different from final
        if normalized_path != final_path and normalized_path != input_path:
            cleanup_temp_files([normalized_path])

        logger.info(f"✅ Audio processing complete: {final_path}")
        return final_path

    except Exception as error:
        logger.error(f"❌ Audio processing failed: {error}")
        # Return original file if processing fails
        return input_path