"""File storage service for uploaded canvas and audio files."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile


class FileStorageService:
    """Service for saving uploaded files to disk with organized directory structure."""

    def __init__(self, upload_root: str) -> None:
        """Initialize file storage service.

        Args:
            upload_root: Root directory for all uploaded files (e.g., "./backend/storage/uploads")
        """
        self.upload_root = Path(upload_root)
        self.upload_root.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file: UploadFile,
        submission_id: str,
        filename: str,
    ) -> str:
        """Save an uploaded file to disk.

        Args:
            file: FastAPI UploadFile object
            submission_id: ID of the submission (used for directory organization)
            filename: Desired filename (e.g., "canvas_clarify.png", "audio_design.webm")

        Returns:
            Relative path to the saved file (e.g., "uploads/abc123/canvas_clarify.png")

        Raises:
            IOError: If file save fails
        """
        # Create submission-specific directory
        submission_dir = self.upload_root / submission_id
        submission_dir.mkdir(parents=True, exist_ok=True)

        # Construct full file path
        file_path = submission_dir / filename

        # Save file to disk
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            raise IOError(f"Failed to save file {filename}: {e}")

        # Return path relative to current working directory for portability
        # This allows the path to work regardless of where the server is started from
        try:
            relative_path = file_path.resolve().relative_to(Path.cwd())
        except ValueError:
            # If file is outside CWD, return absolute path
            relative_path = file_path.resolve()

        # Convert to string with forward slashes for cross-platform compatibility
        return str(relative_path).replace(os.sep, "/")

    async def save_canvas(
        self,
        canvas_file: UploadFile,
        submission_id: str,
        phase: str,
    ) -> str:
        """Save a canvas PNG file.

        Args:
            canvas_file: Uploaded PNG file
            submission_id: Submission ID
            phase: Phase name (e.g., "clarify", "estimate", "design", "explain")

        Returns:
            Relative path to saved file
        """
        filename = f"canvas_{phase}.png"
        return await self.save_file(canvas_file, submission_id, filename)

    async def save_audio(
        self,
        audio_file: Optional[UploadFile],
        submission_id: str,
        phase: str,
    ) -> Optional[str]:
        """Save an audio webm file (if provided).

        Args:
            audio_file: Optional uploaded webm file
            submission_id: Submission ID
            phase: Phase name (e.g., "clarify", "estimate", "design", "explain")

        Returns:
            Relative path to saved file, or None if no audio provided
        """
        if audio_file is None:
            return None

        filename = f"audio_{phase}.webm"
        return await self.save_file(audio_file, submission_id, filename)

    def delete_submission_files(self, submission_id: str) -> None:
        """Delete all files for a submission.

        Args:
            submission_id: Submission ID

        Note:
            This is used for cleanup after processing or on errors.
            Not called automatically - caller must decide when to cleanup.
        """
        submission_dir = self.upload_root / submission_id
        if submission_dir.exists():
            import shutil

            shutil.rmtree(submission_dir)


def get_file_storage_service(upload_root: str) -> FileStorageService:
    """Factory function to create a FileStorageService instance.

    Args:
        upload_root: Root directory for uploads (from environment config)

    Returns:
        FileStorageService instance
    """
    return FileStorageService(upload_root)


__all__ = ["FileStorageService", "get_file_storage_service"]
