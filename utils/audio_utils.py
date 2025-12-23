"""
Audio utility functions for time formatting, duration estimation, and file operations
"""
import zipfile
from io import BytesIO
from datetime import datetime
import re


def format_time(seconds):
    """
    Format seconds as MM:SS

    Args:
        seconds: Time in seconds (float or int)

    Returns:
        str: Formatted time string (MM:SS)
    """
    if seconds is None or seconds < 0:
        return "00:00"

    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def estimate_duration(text):
    """
    Estimate audio duration based on text length
    Uses 150ms per character (same as PWA)

    Args:
        text: Text string

    Returns:
        float: Estimated duration in seconds
    """
    if not text:
        return 0.0

    return len(text) * 0.15


def generate_filename(track, index=None):
    """
    Generate meaningful MP3 filename from track data

    Args:
        track: Dictionary with 'english' and 'korean' keys
        index: Optional track index (for numbering)

    Returns:
        str: Filename like "01_Hello_world.mp3"
    """
    # Get first 30 chars of English text
    english_preview = track.get('english', 'track')[:30]

    # Clean filename (remove special chars, replace spaces with underscores)
    clean_text = re.sub(r'[^\w\s-]', '', english_preview)
    clean_text = re.sub(r'[\s]+', '_', clean_text)

    # Add index prefix if provided
    if index is not None:
        return f"{index+1:02d}_{clean_text}.mp3"
    else:
        return f"{clean_text}.mp3"


def create_zip_from_audio_files(audio_data_list):
    """
    Create ZIP archive from list of audio files

    Args:
        audio_data_list: List of tuples [(audio_bytes, filename), ...]

    Returns:
        bytes: ZIP file contents
    """
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for audio_bytes, filename in audio_data_list:
            zip_file.writestr(filename, audio_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def get_audio_duration_from_bytes(audio_bytes):
    """
    Get actual duration from audio bytes using librosa

    Args:
        audio_bytes: MP3 audio bytes

    Returns:
        float: Duration in seconds
    """
    try:
        import librosa
        import soundfile as sf
        from io import BytesIO
        import tempfile

        # Write to temp file (librosa needs file path for MP3)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            # Load audio
            y, sr = librosa.load(temp_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            return duration
        finally:
            # Clean up temp file
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0.0
