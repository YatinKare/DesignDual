"""File storage service for uploaded canvas and audio files."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile


class FileStorageService:
    """Service for saving uploaded files to disk with organized directory structure."""

    def __init__(self, upload_root: str, max_size_mb: int = 50) -> None:
        """Initialize file storage service.

        Args:
            upload_root: Root directory for all uploaded files (e.g., "./backend/storage/uploads")
            max_size_mb: Maximum file size in megabytes (default: 50 MB)
        """
        self.upload_root = Path(upload_root)
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes

    def validate_file_size(self, file_size: int, filename: str) -> None:
        """Validate that file size is within limits.

        Args:
            file_size: Size of file in bytes
            filename: Name of the file (for error messages)

        Raises:
            HTTPException: If file size exceeds limit
        """
        if file_size > self.max_size_bytes:
            max_size_mb = self.max_size_bytes / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File '{filename}' size ({actual_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb:.0f} MB)",
            )

    def validate_file_type(
        self, content_type: Optional[str], filename: str, expected_types: list[str]
    ) -> None:
        """Validate that file content type matches expected types.

        Args:
            content_type: MIME type from upload (may be None)
            filename: Name of the file
            expected_types: List of allowed MIME types (e.g., ["image/png"])

        Raises:
            HTTPException: If content type is invalid or doesn't match expected types
        """
        if content_type is None:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' has no content type",
            )

        if content_type not in expected_types:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' has invalid type '{content_type}'. Expected one of: {', '.join(expected_types)}",
            )

    async def save_file(
        self,
        file: UploadFile,
        submission_id: str,
        filename: str,
        expected_types: Optional[list[str]] = None,
    ) -> str:
        """Save an uploaded file to disk with validation.

        Args:
            file: FastAPI UploadFile object
            submission_id: ID of the submission (used for directory organization)
            filename: Desired filename (e.g., "canvas_clarify.png", "audio_design.webm")
            expected_types: List of allowed MIME types (e.g., ["image/png"])

        Returns:
            Relative path to the saved file (e.g., "uploads/abc123/canvas_clarify.png")

        Raises:
            HTTPException: If file validation fails
            IOError: If file save fails
        """
        # Validate content type if specified
        if expected_types:
            self.validate_file_type(file.content_type, file.filename or filename, expected_types)

        # Create submission-specific directory
        submission_dir = self.upload_root / submission_id
        submission_dir.mkdir(parents=True, exist_ok=True)

        # Construct full file path
        file_path = submission_dir / filename

        # Read file contents
        try:
            contents = await file.read()
        except Exception as e:
            raise IOError(f"Failed to read file {filename}: {e}")

        # Validate file size
        self.validate_file_size(len(contents), file.filename or filename)

        # Save file to disk
        try:
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
        """Save a canvas PNG file with validation.

        Args:
            canvas_file: Uploaded PNG file
            submission_id: Submission ID
            phase: Phase name (e.g., "clarify", "estimate", "design", "explain")

        Returns:
            Relative path to saved file

        Raises:
            HTTPException: If file validation fails (invalid type or size)
        """
        filename = f"canvas_{phase}.png"
        return await self.save_file(
            canvas_file,
            submission_id,
            filename,
            expected_types=["image/png"],
        )

    async def save_audio(
        self,
        audio_file: Optional[UploadFile],
        submission_id: str,
        phase: str,
    ) -> Optional[str]:
        """Save an audio webm file (if provided) with validation.

        Args:
            audio_file: Optional uploaded webm file
            submission_id: Submission ID
            phase: Phase name (e.g., "clarify", "estimate", "design", "explain")

        Returns:
            Relative path to saved file, or None if no audio provided

        Raises:
            HTTPException: If file validation fails (invalid type or size)
        """
        if audio_file is None:
            return None

        filename = f"audio_{phase}.webm"
        return await self.save_file(
            audio_file,
            submission_id,
            filename,
            expected_types=["audio/webm", "video/webm"],  # webm can be audio or video MIME type
        )

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


def get_file_storage_service(upload_root: str, max_size_mb: int = 50) -> FileStorageService:
    """Factory function to create a FileStorageService instance.

    Args:
        upload_root: Root directory for uploads (from environment config)
        max_size_mb: Maximum file size in megabytes (default: 50 MB)

    Returns:
        FileStorageService instance
    """
    return FileStorageService(upload_root, max_size_mb)


__all__ = ["FileStorageService", "get_file_storage_service"]
