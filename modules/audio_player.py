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
    audio_key = f"audio_player_{play_count}"
    st.audio(audio_bytes, format='audio/mp3', autoplay=True, start_time=0)

    # Add JavaScript to detect audio end and trigger auto-advance
    auto_play = st.session_state.get('auto_play', False)
    repeat_mode = st.session_state.get('repeat_mode', 'none')
    
    if auto_play:
        _inject_audio_end_listener(audio_key, repeat_mode)

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


def _inject_audio_end_listener(audio_key, repeat_mode):
    """
    Inject JavaScript to listen for audio ended event and trigger auto-advance
    Uses st.markdown with unsafe_allow_html to inject directly into main page (no iframe)
    
    Args:
        audio_key: Streamlit audio component key
        repeat_mode: Current repeat mode ('none', 'one', 'all')
    """
    # JavaScript code to detect audio end and trigger auto-advance
    # This runs directly in the main page, not in an iframe
    js_code = f"""
<script>
(function() {{
    let listenerAttached = false;
    let audioEnded = false;
    const listenerKey = 'audio_listener_{audio_key}';
    
    function attachAudioListener() {{
        if (listenerAttached) return;
        
        // Find audio elements directly in the main document
        const allAudios = document.querySelectorAll('audio');
        
        if (allAudios.length === 0) {{
            // Audio not found yet, retry
            console.log('Audio element not found, will retry...');
            return;
        }}
        
        // Use the most recently added audio (last in list)
        const targetAudio = allAudios[allAudios.length - 1];
        
        // Check if already has our listener
        if (targetAudio.dataset[listenerKey] === 'true') {{
            return;
        }}
        
        targetAudio.dataset[listenerKey] = 'true';
        
        targetAudio.addEventListener('ended', function() {{
            if (audioEnded) return; // Prevent multiple triggers
            audioEnded = true;
            
            console.log('Audio playback ended - triggering auto-advance');
            
            // Trigger Streamlit rerun via URL parameter
            try {{
                const currentUrl = window.location.href;
                const url = new URL(currentUrl);
                // Remove existing auto_advance param
                url.searchParams.delete('auto_advance');
                // Add new one with timestamp to force reload
                url.searchParams.set('auto_advance', Date.now().toString());
                console.log('Reloading with URL:', url.toString());
                window.location.href = url.toString();
            }} catch(e) {{
                console.log('Error triggering reload:', e);
            }}
        }}, {{ once: false }});
        
        listenerAttached = true;
        console.log('Audio end listener attached successfully to:', targetAudio);
    }}
    
    // Try to attach listener immediately
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', attachAudioListener);
    }} else {{
        attachAudioListener();
    }}
    
    // Retry with delays to catch dynamically added elements
    setTimeout(attachAudioListener, 300);
    setTimeout(attachAudioListener, 1000);
    setTimeout(attachAudioListener, 2000);
}})();
</script>
"""
    
    # Inject the JavaScript directly into the main page (no iframe)
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Check for auto-advance trigger from query parameters
    # Only process if we haven't already processed this trigger
    query_params = st.query_params
    auto_advance_param = query_params.get('auto_advance')
    last_processed = st.session_state.get('_last_auto_advance', '')
    
    if auto_advance_param and auto_advance_param != last_processed:
        # Mark this trigger as processed to prevent duplicate processing
        st.session_state['_last_auto_advance'] = auto_advance_param
        
        # Handle the auto-advance
        _handle_audio_ended(repeat_mode)


def _handle_audio_ended(repeat_mode):
    """
    Handle audio ended event - advance to next track based on repeat mode
    
    Args:
        repeat_mode: Current repeat mode ('none', 'one', 'all')
    """
    total_tracks = len(st.session_state.tracks)
    current_track = st.session_state.current_track
    
    # Use handle_track_end to determine next track (same module, no import needed)
    next_track, should_play = handle_track_end(current_track, total_tracks, repeat_mode)
    
    if should_play:
        # Update track and force audio refresh
        # For Repeat One mode, next_track will be the same as current_track
        st.session_state.current_track = next_track
        st.session_state.play_count = st.session_state.get('play_count', 0) + 1
        st.rerun()


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
