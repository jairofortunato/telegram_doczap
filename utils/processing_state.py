"""
Processing State Manager for DOCZAP
Prevents duplicate processing of audio messages
"""

import time
from typing import Dict, Set, Optional
from loguru import logger
import threading


class ProcessingStateManager:
    """
    Manages processing state to prevent duplicate audio processing
    Tracks which messages are currently being processed and recently completed
    """

    def __init__(self, cleanup_interval: int = 300):
        """
        Initialize processing state manager

        Args:
            cleanup_interval: Seconds to keep completed messages in memory (default 5 minutes)
        """
        self.processing: Dict[str, float] = {}  # file_id -> start_timestamp
        self.completed: Dict[str, float] = {}   # file_id -> completion_timestamp
        self.cleanup_interval = cleanup_interval
        self.lock = threading.Lock()

        logger.info(f"🔒 Processing state manager initialized (cleanup interval: {cleanup_interval}s)")

    def is_processing(self, file_id: str) -> bool:
        """Check if a file is currently being processed"""
        with self.lock:
            return file_id in self.processing

    def is_completed(self, file_id: str) -> bool:
        """Check if a file was recently completed"""
        with self.lock:
            if file_id in self.completed:
                # Check if completion is recent (within cleanup interval)
                time_since_completion = time.time() - self.completed[file_id]
                if time_since_completion < self.cleanup_interval:
                    return True
                else:
                    # Clean up old entry
                    del self.completed[file_id]
            return False

    def start_processing(self, file_id: str) -> bool:
        """
        Mark a file as being processed

        Returns:
            True if processing can start (not already processing/completed)
            False if already processing or recently completed
        """
        with self.lock:
            # Check if already processing
            if file_id in self.processing:
                time_processing = time.time() - self.processing[file_id]
                logger.warning(f"⚠️ File {file_id} is already being processed ({time_processing:.1f}s ago)")
                return False

            # Check if recently completed
            if file_id in self.completed:
                time_since_completion = time.time() - self.completed[file_id]
                if time_since_completion < self.cleanup_interval:
                    logger.warning(f"⚠️ File {file_id} was already processed ({time_since_completion:.1f}s ago)")
                    return False
                else:
                    # Clean up old entry
                    del self.completed[file_id]

            # Mark as processing
            self.processing[file_id] = time.time()
            logger.info(f"✅ Started processing file {file_id}")
            return True

    def finish_processing(self, file_id: str, success: bool = True):
        """
        Mark a file as finished processing

        Args:
            file_id: The file ID that finished processing
            success: Whether processing was successful
        """
        with self.lock:
            if file_id in self.processing:
                processing_time = time.time() - self.processing[file_id]
                del self.processing[file_id]

                # Add to completed if successful
                if success:
                    self.completed[file_id] = time.time()
                    logger.info(f"✅ Finished processing file {file_id} (took {processing_time:.1f}s)")
                else:
                    logger.warning(f"❌ Failed processing file {file_id} (took {processing_time:.1f}s)")
            else:
                logger.warning(f"⚠️ Tried to finish processing file {file_id} but it wasn't marked as processing")

    def cleanup_old_entries(self):
        """Clean up old completed entries"""
        with self.lock:
            current_time = time.time()

            # Clean up old completed entries
            completed_to_remove = [
                file_id for file_id, timestamp in self.completed.items()
                if current_time - timestamp > self.cleanup_interval
            ]

            for file_id in completed_to_remove:
                del self.completed[file_id]

            if completed_to_remove:
                logger.info(f"🧹 Cleaned up {len(completed_to_remove)} old completed entries")

            # Clean up stuck processing entries (over 10 minutes old)
            stuck_timeout = 600  # 10 minutes
            stuck_to_remove = [
                file_id for file_id, timestamp in self.processing.items()
                if current_time - timestamp > stuck_timeout
            ]

            for file_id in stuck_to_remove:
                processing_time = current_time - self.processing[file_id]
                del self.processing[file_id]
                logger.warning(f"⚠️ Removed stuck processing entry for {file_id} (was processing for {processing_time:.1f}s)")

            if stuck_to_remove:
                logger.warning(f"🧹 Cleaned up {len(stuck_to_remove)} stuck processing entries")

    def get_stats(self) -> Dict:
        """Get current processing statistics"""
        with self.lock:
            return {
                "currently_processing": len(self.processing),
                "recently_completed": len(self.completed),
                "processing_files": list(self.processing.keys()),
                "completed_files": list(self.completed.keys())
            }

    def reset(self):
        """Reset all state (useful for testing)"""
        with self.lock:
            self.processing.clear()
            self.completed.clear()
            logger.info("🔄 Processing state reset")
