"""Audio transcription service using Gemini API.

This module provides functionality to transcribe audio files using Google's
Gemini API. It supports both the Files API (for larger files) and inline
data (for smaller files < 20MB).
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types


# Supported audio MIME types per Gemini docs
# Note: .m4a and .webm are added for DesignDual workflow compatibility
# - .m4a is MPEG-4 container with AAC audio (maps to audio/mp4)
# - .webm typically uses Opus codec (maps to audio/webm)
SUPPORTED_AUDIO_MIMES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".aiff": "audio/aiff",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".webm": "audio/webm",
}

# Max size for inline data (in bytes) - 20MB
MAX_INLINE_SIZE = 20 * 1024 * 1024


def get_genai_client() -> genai.Client:
    """Create and return a Gemini API client.

    The client uses the GOOGLE_API_KEY environment variable.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your-google-api-key":
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set to a valid API key"
        )
    return genai.Client(api_key=api_key)


def get_mime_type(file_path: str | Path) -> str:
    """Determine the MIME type based on file extension.

    Args:
        file_path: Path to the audio file.

    Returns:
        MIME type string.

    Raises:
        ValueError: If the file extension is not supported.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_AUDIO_MIMES:
        raise ValueError(
            f"Unsupported audio format: {ext}. "
            f"Supported formats: {list(SUPPORTED_AUDIO_MIMES.keys())}"
        )

    return SUPPORTED_AUDIO_MIMES[ext]


async def transcribe_audio(
    file_path: str | Path,
    model: str = "gemini-2.5-flash",
    prompt: str = "Generate a transcript of the speech.",
) -> str:
    """Transcribe an audio file using Gemini API.

    This function handles both small files (inline data) and larger files
    (via Files API upload).

    Args:
        file_path: Path to the audio file to transcribe.
        model: Gemini model to use for transcription.
        prompt: Prompt to send with the audio.

    Returns:
        The transcribed text from the audio.

    Raises:
        FileNotFoundError: If the audio file doesn't exist.
        ValueError: If the audio format is not supported.
        Exception: If transcription fails.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    client = get_genai_client()
    mime_type = get_mime_type(path)
    file_size = path.stat().st_size

    # Use inline data for small files, Files API for larger ones
    if file_size < MAX_INLINE_SIZE:
        return await _transcribe_inline(client, path, mime_type, model, prompt)
    else:
        return await _transcribe_with_upload(client, path, mime_type, model, prompt)


async def _transcribe_inline(
    client: genai.Client,
    file_path: Path,
    mime_type: str,
    model: str,
    prompt: str,
) -> str:
    """Transcribe using inline audio data for small files.

    Args:
        client: Gemini API client.
        file_path: Path to the audio file.
        mime_type: MIME type of the audio.
        model: Model to use.
        prompt: Transcription prompt.

    Returns:
        Transcribed text.
    """
    audio_bytes = file_path.read_bytes()

    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )

    return response.text


async def _transcribe_with_upload(
    client: genai.Client,
    file_path: Path,
    mime_type: str,
    model: str,
    prompt: str,
) -> str:
    """Transcribe using Files API upload for larger files.

    Args:
        client: Gemini API client.
        file_path: Path to the audio file.
        mime_type: MIME type of the audio.
        model: Model to use.
        prompt: Transcription prompt.

    Returns:
        Transcribed text.
    """
    # Upload the file
    uploaded_file = client.files.upload(file=str(file_path))

    try:
        response = client.models.generate_content(
            model=model,
            contents=[prompt, uploaded_file],
        )
        return response.text
    finally:
        # Clean up uploaded file
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            # Ignore cleanup errors
            pass


async def transcribe_audio_bytes(
    audio_bytes: bytes,
    mime_type: str,
    model: str = "gemini-2.5-flash",
    prompt: str = "Generate a transcript of the speech.",
) -> str:
    """Transcribe audio from raw bytes.

    Useful when audio data is already in memory (e.g., from file upload).

    Args:
        audio_bytes: Raw audio data.
        mime_type: MIME type of the audio data.
        model: Gemini model to use.
        prompt: Transcription prompt.

    Returns:
        Transcribed text.

    Raises:
        ValueError: If MIME type is not supported.
    """
    # Validate MIME type
    valid_mimes = set(SUPPORTED_AUDIO_MIMES.values())
    if mime_type not in valid_mimes:
        raise ValueError(
            f"Unsupported MIME type: {mime_type}. Supported: {list(valid_mimes)}"
        )

    client = get_genai_client()

    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )

    return response.text


def is_supported_audio_format(file_path: str | Path) -> bool:
    """Check if a file has a supported audio format.

    Args:
        file_path: Path to check.

    Returns:
        True if the file extension is supported, False otherwise.
    """
    path = Path(file_path)
    return path.suffix.lower() in SUPPORTED_AUDIO_MIMES


async def transcribe_audio_files_parallel(
    file_paths: list[str | Path | None],
    model: str = "gemini-2.5-flash",
    prompt: str = "Generate a transcript of the speech.",
) -> list[str | None]:
    """Transcribe multiple audio files in parallel.

    Designed for the 4-phase interview workflow where each phase may have
    an optional audio file. Handles None values gracefully.

    Args:
        file_paths: List of up to 4 audio file paths. None values are allowed
                   for phases without audio.
        model: Gemini model to use for transcription.
        prompt: Prompt to send with each audio file.

    Returns:
        List of transcripts in the same order as input. None for files that
        were None or failed to transcribe.

    Example:
        >>> transcripts = await transcribe_audio_files_parallel([
        ...     "clarify.mp3",
        ...     None,  # No audio for estimate phase
        ...     "design.mp3",
        ...     "explain.mp3",
        ... ])
        >>> # Returns: ["transcript1", None, "transcript2", "transcript3"]
    """
    async def safe_transcribe(file_path: str | Path | None) -> str | None:
        """Transcribe a single file, returning None on failure or if path is None."""
        if file_path is None:
            return None

        try:
            return await transcribe_audio(file_path, model=model, prompt=prompt)
        except Exception as e:
            # Log error but don't fail the entire batch
            import logging
            logging.warning(f"Failed to transcribe {file_path}: {e}")
            return None

    # Run all transcriptions in parallel
    tasks = [safe_transcribe(path) for path in file_paths]
    results = await asyncio.gather(*tasks)

    return list(results)

