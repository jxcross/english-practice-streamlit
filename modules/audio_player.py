"""
Audio player module for playback and MP3 download functionality
"""
import streamlit as st
from utils.audio_utils import format_time, generate_filename, get_audio_duration_from_bytes


def render_audio_player(audio_bytes, track, show_download=True):
    """
    Render audio player with controls and optional download button

    Args:
        audio_bytes: MP3 audio bytes
        track: Track dictionary {'english': '...', 'korean': '...'}
        show_download: Whether to show download button

    Returns:
        None
    """
    if not audio_bytes:
        st.warning("No audio generated")
        return

    # Display audio player with autoplay and start time to force refresh
    # Adding start_time parameter helps browser treat each playback as unique
    play_count = st.session_state.get('play_count', 0)
    st.audio(audio_bytes, format='audio/mp3', autoplay=True, start_time=0)

    # Add a unique marker to help Streamlit detect changes
    st.markdown(f'<!-- playback_{play_count} -->', unsafe_allow_html=True)

    # Get actual duration
    try:
        duration = get_audio_duration_from_bytes(audio_bytes)
        st.caption(f"Duration: {format_time(duration)}")
    except Exception:
        pass

    # Download button
    if show_download:
        render_download_button(track, audio_bytes)


def render_download_button(track, audio_bytes, index=None):
    """
    Render download button for single track

    Args:
        track: Track dictionary
        audio_bytes: MP3 audio bytes
        index: Optional track index for filename

    Returns:
        None
    """
    if not audio_bytes:
        return

    filename = generate_filename(track, index)

    st.download_button(
        label="⬇️ Download MP3",
        data=audio_bytes,
        file_name=filename,
        mime="audio/mpeg",
        key=f"download_{track.get('english', 'track')[:20]}_{index}"
    )


def create_playlist_zip(tracks, tts_engine, selected_voice):
    """
    Generate all TTS audio and package as ZIP

    Args:
        tracks: List of track dictionaries
        tts_engine: TTSEngine instance
        selected_voice: Voice name for TTS

    Returns:
        bytes: ZIP file contents
    """
    from utils.audio_utils import create_zip_from_audio_files
    import streamlit as st

    audio_files = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, track in enumerate(tracks):
        status_text.text(f"Generating audio {i+1}/{len(tracks)}: {track['english'][:50]}...")

        try:
            # Generate audio
            audio_bytes, _, _ = tts_engine.generate_audio(
                text=track['english'],
                voice=selected_voice
            )

            # Create filename
            filename = generate_filename(track, i)

            audio_files.append((audio_bytes, filename))

        except Exception as e:
            st.warning(f"Error generating audio for track {i+1}: {str(e)}")

        # Update progress
        progress_bar.progress((i + 1) / len(tracks))

    status_text.text("Creating ZIP archive...")

    # Create ZIP
    zip_bytes = create_zip_from_audio_files(audio_files)

    progress_bar.empty()
    status_text.empty()

    return zip_bytes


def handle_track_end(current_track, total_tracks, repeat_mode):
    """
    Handle track end based on repeat mode

    Args:
        current_track: Current track index
        total_tracks: Total number of tracks
        repeat_mode: Repeat mode ('none', 'one', 'all')

    Returns:
        tuple: (next_track_index, should_play)
    """
    if repeat_mode == 'one':
        # Replay same track
        return current_track, True

    elif repeat_mode == 'all':
        # Next track or loop to first
        next_track = (current_track + 1) % total_tracks
        return next_track, True

    else:  # 'none'
        # Stop at end of playlist
        if current_track < total_tracks - 1:
            return current_track + 1, True
        else:
            return current_track, False
