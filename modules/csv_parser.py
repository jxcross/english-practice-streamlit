"""
CSV and text parsing utilities for track data
"""
import pandas as pd
import io


def parse_csv_file(file_content):
    """
    Parse CSV file content

    Args:
        file_content: File-like object or bytes

    Returns:
        tuple: (tracks_list, error_message)
            tracks_list: List of track dictionaries [{'english': '...', 'korean': '...'}, ...]
            error_message: Error message if parsing failed, None otherwise
    """
    try:
        # Read CSV
        if isinstance(file_content, bytes):
            file_content = io.BytesIO(file_content)

        df = pd.read_csv(file_content)

        # Validate columns
        if 'english' not in df.columns or 'korean' not in df.columns:
            return None, "CSV must have 'english' and 'korean' columns"

        # Convert to list of dictionaries
        tracks = []
        for _, row in df.iterrows():
            english = str(row['english']).strip() if pd.notna(row['english']) else ''
            korean = str(row['korean']).strip() if pd.notna(row['korean']) else ''

            if english and korean:  # Only include rows with both values
                tracks.append({
                    'english': english,
                    'korean': korean
                })

        if not tracks:
            return None, "No valid tracks found in CSV"

        return tracks, None

    except Exception as e:
        return None, f"Error parsing CSV: {str(e)}"


def parse_text_input(text):
    """
    Parse text input (supports CSV format or line-by-line format)

    Formats supported:
    1. CSV: "english text","korean text"
    2. Line-by-line: alternating English and Korean lines

    Args:
        text: Text string

    Returns:
        tuple: (tracks_list, error_message)
    """
    if not text or not text.strip():
        return None, "No text provided"

    try:
        lines = text.strip().split('\n')

        # Try to detect format
        if _is_csv_format(lines):
            return _parse_csv_text(text)
        else:
            return _parse_line_by_line(lines)

    except Exception as e:
        return None, f"Error parsing text: {str(e)}"


def _is_csv_format(lines):
    """
    Detect if text is in CSV format

    Args:
        lines: List of text lines

    Returns:
        bool: True if appears to be CSV format
    """
    if not lines:
        return False

    # Check first line for CSV header
    first_line = lines[0].strip().lower()
    if 'english' in first_line and 'korean' in first_line:
        return True

    # Check if lines contain commas (CSV indicator)
    comma_count = sum(1 for line in lines[:5] if ',' in line)
    return comma_count >= len(lines[:5]) * 0.5  # At least 50% of first 5 lines have commas


def _parse_csv_text(text):
    """Parse text in CSV format"""
    try:
        df = pd.read_csv(io.StringIO(text))

        if 'english' not in df.columns or 'korean' not in df.columns:
            return None, "CSV must have 'english' and 'korean' columns"

        tracks = []
        for _, row in df.iterrows():
            english = str(row['english']).strip() if pd.notna(row['english']) else ''
            korean = str(row['korean']).strip() if pd.notna(row['korean']) else ''

            if english and korean:
                tracks.append({
                    'english': english,
                    'korean': korean
                })

        if not tracks:
            return None, "No valid tracks found"

        return tracks, None

    except Exception as e:
        return None, f"Error parsing CSV text: {str(e)}"


def _parse_line_by_line(lines):
    """
    Parse text in line-by-line format (alternating English/Korean)

    Args:
        lines: List of text lines

    Returns:
        tuple: (tracks_list, error_message)
    """
    try:
        tracks = []

        # Remove empty lines
        lines = [line.strip() for line in lines if line.strip()]

        # Check if we have an even number of lines
        if len(lines) % 2 != 0:
            return None, "Line-by-line format requires an even number of lines (alternating English and Korean)"

        # Parse alternating lines
        for i in range(0, len(lines), 2):
            english = lines[i].strip()
            korean = lines[i + 1].strip() if i + 1 < len(lines) else ''

            if english and korean:
                tracks.append({
                    'english': english,
                    'korean': korean
                })

        if not tracks:
            return None, "No valid tracks found"

        return tracks, None

    except Exception as e:
        return None, f"Error parsing line-by-line text: {str(e)}"


def validate_tracks(tracks):
    """
    Validate tracks list

    Args:
        tracks: List of track dictionaries

    Returns:
        tuple: (is_valid, error_message)
    """
    if not tracks:
        return False, "No tracks provided"

    if not isinstance(tracks, list):
        return False, "Tracks must be a list"

    for i, track in enumerate(tracks):
        if not isinstance(track, dict):
            return False, f"Track {i+1} is not a dictionary"

        if 'english' not in track or 'korean' not in track:
            return False, f"Track {i+1} missing 'english' or 'korean' field"

        if not track['english'] or not track['korean']:
            return False, f"Track {i+1} has empty 'english' or 'korean' field"

    return True, None
