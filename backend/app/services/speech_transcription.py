"""
Speech-to-text using SpeechRecognition (Google Web Speech API).
Browser WebM/MP4 is converted to 16 kHz mono WAV via ffmpeg stdin/stdout only
(no ffprobe). Uses system ffmpeg if on PATH, else the binary shipped with imageio-ffmpeg.
"""

from __future__ import annotations

import io
import logging
import re
import shutil
import subprocess
from pathlib import Path

import speech_recognition as sr

from app.config import Settings

logger = logging.getLogger(__name__)

# ffmpeg -f <demuxer> for pipe input (must match container, not ffprobe)
_FFMPEG_DEMUX: dict[str, str] = {
    "webm": "webm",
    "wav": "wav",
    "mp3": "mp3",
    "mp4": "mp4",
    "m4a": "mp4",
    "ogg": "ogg",
    "oga": "ogg",
    "flac": "flac",
    "mpeg": "mp3",
    "mpga": "mp3",
}


class TranscriptionError(Exception):
    """Failed to turn audio into text."""


def _sniff_format(filename: str) -> str:
    ext = Path(filename or "audio.webm").suffix.lower().lstrip(".")
    if ext in _FFMPEG_DEMUX:
        if ext == "oga":
            return "ogg"
        return ext
    return "webm"


def _resolve_ffmpeg() -> str | None:
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _decode_to_wav_pcm16k_mono(raw: bytes, container_fmt: str) -> bytes:
    ffmpeg = _resolve_ffmpeg()
    if not ffmpeg:
        raise TranscriptionError(
            "ffmpeg is not available. Install ffmpeg (e.g. brew install ffmpeg) "
            "or ensure imageio-ffmpeg is installed (pip install imageio-ffmpeg)."
        )
    demux = _FFMPEG_DEMUX.get(container_fmt, "webm")
    cmd = [
        ffmpeg,
        "-nostdin",
        "-loglevel",
        "error",
        "-f",
        demux,
        "-i",
        "pipe:0",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        "-acodec",
        "pcm_s16le",
        "pipe:1",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=raw,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError as e:
        raise TranscriptionError("ffmpeg executable not found.") from e
    except subprocess.TimeoutExpired as e:
        raise TranscriptionError("Audio conversion timed out.") from e

    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")[:800]
        logger.warning("ffmpeg decode failed (demux=%s): %s", demux, err)
        raise TranscriptionError(
            "Could not decode this audio format. Try recording again, or use text entry."
        )
    out = proc.stdout or b""
    if len(out) < 100:
        raise TranscriptionError("Converted audio was too short or empty.")
    return out


def _recognize_wav(wav_bytes: bytes, settings: Settings) -> str:
    buf = io.BytesIO(wav_bytes)
    recognizer = sr.Recognizer()
    with sr.AudioFile(buf) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(
        audio_data,
        language=settings.speech_recognition_language,
    )


def transcribe_audio(file_content: bytes, filename: str, settings: Settings) -> str:
    if settings.mock_whisper:
        return settings.mock_whisper_text
    if not file_content:
        raise TranscriptionError("Empty audio payload")

    fmt = _sniff_format(filename)

    # Already WAV: try recognition first without ffmpeg
    if fmt == "wav":
        try:
            text = _recognize_wav(file_content, settings)
            text = (text or "").strip()
            if text:
                return re.sub(r"\s+", " ", text)
        except sr.UnknownValueError as e:
            raise TranscriptionError("Could not understand the speech in this recording.") from e
        except sr.RequestError as e:
            raise TranscriptionError(f"Speech recognition service error: {e}") from e
        except Exception:
            logger.debug("Direct WAV decode failed, trying ffmpeg normalize", exc_info=True)

    try:
        wav_bytes = _decode_to_wav_pcm16k_mono(file_content, fmt)
        text = _recognize_wav(wav_bytes, settings)
    except TranscriptionError:
        raise
    except sr.UnknownValueError as e:
        raise TranscriptionError("Could not understand the speech in this recording.") from e
    except sr.RequestError as e:
        raise TranscriptionError(f"Speech recognition service error: {e}") from e
    except Exception as e:
        logger.exception("Unexpected error during speech recognition")
        raise TranscriptionError(str(e)) from e

    text = (text or "").strip()
    if not text:
        raise TranscriptionError("Transcription was empty.")
    return re.sub(r"\s+", " ", text)
