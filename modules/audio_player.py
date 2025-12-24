"""
Audio player module for playback and MP3 download functionality
"""
import streamlit as st
import streamlit.components.v1 as components
from utils.audio_utils import format_time, generate_filename, get_audio_duration_from_bytes


def render_audio_player(audio_bytes, track, show_download=True, use_custom_component=False):
    """
    Render audio player using st.audio() with auto-advance support

    Args:
        audio_bytes: MP3 audio bytes
        track: Track dictionary {'english': '...', 'korean': '...'}
        show_download: Whether to show download button
        use_custom_component: Ignored (kept for compatibility)

    Returns:
        None
    """
    if not audio_bytes:
        st.warning("No audio generated")
        return

    # Get current state
    play_count = st.session_state.get('play_count', 0)
    repeat_mode = st.session_state.get('repeat_mode', 'none')
    auto_play = st.session_state.get('auto_play', False)
    
    # Get audio duration
    duration = None
    try:
        duration = get_audio_duration_from_bytes(audio_bytes)
        st.caption(f"Duration: {format_time(duration)}")
    except Exception:
        pass

    # Render audio player using st.audio()
    # Note: st.audio() doesn't support 'key' parameter
    # Use play_count to create unique identifier for JavaScript
    audio_key = f"audio_player_{play_count}"
    st.audio(audio_bytes, format="audio/mp3", autoplay=auto_play)

    # Inject JavaScript to detect audio end and handle repeat mode
    _inject_audio_end_listener(audio_key, repeat_mode)

    # Download button
    if show_download:
        render_download_button(track, audio_bytes)


def _inject_audio_end_listener(audio_key, repeat_mode):
    """
    Inject JavaScript to listen for audio ended event and trigger auto-advance
    
    Args:
        audio_key: Streamlit audio component key
        repeat_mode: Current repeat mode ('none', 'one', 'all')
    """
    # JavaScript code to detect audio end and trigger auto-advance
    js_code = f"""
<script>
(function() {{
    const audioKey = '{audio_key}';
    const repeatMode = '{repeat_mode}';
    let processedAudio = null;
    let hasEnded = false;
    
    function findAndAttachToAudio() {{
        // Find the audio element created by st.audio()
        const audioElements = document.querySelectorAll('audio');
        
        if (audioElements.length === 0) {{
            // Audio not ready yet, retry
            setTimeout(findAndAttachToAudio, 100);
            return;
        }}
        
        // Get the most recent audio element (should be the one we just created)
        const audio = audioElements[audioElements.length - 1];
        
        // Skip if already processed
        if (processedAudio === audio) {{
            return;
        }}
        
        processedAudio = audio;
        hasEnded = false;
        
        console.log('Attaching audio end listener to audio element, repeat mode:', repeatMode);
        
        // Listen for 'ended' event
        audio.addEventListener('ended', function() {{
            if (hasEnded) return; // Prevent duplicate triggers
            hasEnded = true;
            console.log('Audio playback ended, repeat mode:', repeatMode);
            
            // Handle repeat modes
            if (repeatMode === 'one') {{
                // Repeat One: restart current track
                console.log('Repeat One: restarting current track');
                audio.currentTime = 0;
                audio.play().catch(e => console.log('Error restarting audio:', e));
                hasEnded = false; // Reset flag for next play
            }} else {{
                // Repeat All / None: notify Streamlit to advance to next track
                console.log('Repeat ' + repeatMode + ': triggering auto-advance');
            triggerAutoAdvance();
            }}
        }}, {{ once: false }});
        
        // Also monitor timeupdate as a fallback
        let lastCheckTime = 0;
        audio.addEventListener('timeupdate', function() {{
            if (hasEnded) return;
            
            const currentTime = audio.currentTime;
            const duration = audio.duration;
            const isPlaying = !audio.paused;
            
            // Check if audio has finished (within 0.1 seconds of end)
            if (duration && duration > 0 && currentTime >= duration - 0.1 && isPlaying) {{
                if (!hasEnded) {{
                    hasEnded = true;
                    console.log('Audio finished (timeupdate fallback), repeat mode:', repeatMode);
                    
                    if (repeatMode === 'one') {{
                        audio.currentTime = 0;
                        audio.play().catch(e => console.log('Error restarting audio:', e));
                        hasEnded = false;
                    }} else {{
                    triggerAutoAdvance();
                    }}
                }}
            }}
            
            lastCheckTime = currentTime;
        }});
    }}
        
        function triggerAutoAdvance() {{
            // Trigger Streamlit rerun via URL parameter
            try {{
            const url = new URL(window.location.href);
            const timestamp = Date.now().toString();
            
            // Remove existing audio_end param
            url.searchParams.delete('audio_end');
                // Add new one with timestamp to force reload
            url.searchParams.set('audio_end', timestamp);
            url.searchParams.set('repeat_mode', repeatMode);
            
            console.log('Triggering auto-advance with URL:', url.toString());
            window.location.href = url.toString();
        }} catch(e) {{
            console.error('Error triggering auto-advance:', e);
        }}
    }}
    
    // Start looking for audio element
    // Use MutationObserver to detect when audio is added to DOM
                const observer = new MutationObserver(function(mutations) {{
                    let shouldCheck = false;
                    mutations.forEach(function(mutation) {{
                        if (mutation.addedNodes.length > 0) {{
                            mutation.addedNodes.forEach(function(node) {{
                                if (node.nodeType === 1) {{ // Element node
                                    if (node.tagName === 'AUDIO' || (node.querySelector && node.querySelector('audio'))) {{
                                        shouldCheck = true;
                                    }}
                                }}
                            }});
                        }}
                    }});
                    
                    if (shouldCheck) {{
            setTimeout(findAndAttachToAudio, 100);
                    }}
                }});
                
                // Start observing
    if (document.body) {{
        observer.observe(document.body, {{
                    childList: true,
                    subtree: true
        }});
    }}
    
    // Also check immediately and with delays
    findAndAttachToAudio();
    setTimeout(findAndAttachToAudio, 200);
    setTimeout(findAndAttachToAudio, 500);
    setTimeout(findAndAttachToAudio, 1000);
}})();
</script>
"""
    
    # Inject the JavaScript using components.html
    components.html(js_code, height=0)
    
    # Check for audio_end event from query parameters
    query_params = st.query_params
    audio_end_param = query_params.get('audio_end')
    url_repeat_mode = query_params.get('repeat_mode')
    
    if audio_end_param:
        # Use a session state flag to prevent re-processing
        last_timestamp = st.session_state.get('_last_ended_timestamp', 0)
        current_timestamp = int(audio_end_param) if audio_end_param.isdigit() else 0

        if current_timestamp != last_timestamp:
            st.session_state['_last_ended_timestamp'] = current_timestamp
            print(f"[DEBUG] Audio end event detected: timestamp={current_timestamp}, repeat_mode={url_repeat_mode}")
            
            # Use repeat mode from URL (most recent) or session state
            effective_repeat_mode = url_repeat_mode if url_repeat_mode else repeat_mode
            
            # Remove the parameters to prevent re-processing
            params = dict(st.query_params)
            params.pop('audio_end', None)
            params.pop('repeat_mode', None)
            st.query_params.update(params)
            
            # Handle audio ended based on repeat mode
            if effective_repeat_mode in ['all', 'none']:
                _handle_audio_ended(effective_repeat_mode)
            else:
                print(f"[DEBUG] Repeat mode is '{effective_repeat_mode}', skipping auto-advance")


def _handle_audio_ended(repeat_mode):
    """
    Handle audio ended event - advance to next track based on repeat mode

    Args:
        repeat_mode: Current repeat mode ('none', 'one', 'all')
    """
    total_tracks = len(st.session_state.tracks)
    current_track = st.session_state.current_track

    print(f"[DEBUG] _handle_audio_ended called: current_track={current_track}, total={total_tracks}, mode={repeat_mode}")

    # Use handle_track_end to determine next track (same module, no import needed)
    next_track, should_play = handle_track_end(current_track, total_tracks, repeat_mode)

    print(f"[DEBUG] handle_track_end returned: next_track={next_track}, should_play={should_play}")

    if should_play:
        # Update track and force audio refresh
        # For Repeat One mode, next_track will be the same as current_track
        st.session_state.current_track = next_track
        st.session_state.play_count = st.session_state.get('play_count', 0) + 1
        
        # Enable auto-play when advancing via repeat all/one to ensure continuous playback
        if repeat_mode in ['all', 'one']:
            st.session_state.auto_play = True
        
        print(f"[DEBUG] Calling st.rerun() to play track {next_track}")
        st.rerun()
    else:
        print(f"[DEBUG] should_play is False, stopping playback")


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
