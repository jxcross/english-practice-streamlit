"""
Audio player module for playback and MP3 download functionality
"""
import streamlit as st
import streamlit.components.v1 as components
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

    import base64

    # Convert audio bytes to base64 for embedding
    audio_b64 = base64.b64encode(audio_bytes).decode()

    # Get current state
    play_count = st.session_state.get('play_count', 0)
    repeat_mode = st.session_state.get('repeat_mode', 'none')

    # Create custom HTML audio player with Streamlit communication
    html_code = f"""
    <style>
        audio {{
            width: 100%;
            margin: 10px 0;
        }}
    </style>
    <audio id="audio-player-{play_count}" controls autoplay>
        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    <script>
        (function() {{
            const audio = document.getElementById('audio-player-{play_count}');
            const repeatMode = '{repeat_mode}';
            let hasEnded = false;

            console.log('Custom audio player initialized, repeat mode:', repeatMode);

            // Play audio
            audio.play().catch(e => console.log('Autoplay blocked:', e));

            // Monitor progress
            audio.addEventListener('timeupdate', function() {{
                if (Math.floor(audio.currentTime) % 5 === 0) {{
                    console.log('Audio progress:', audio.currentTime.toFixed(1), '/', audio.duration.toFixed(1));
                }}
            }});

            // Handle audio end - use Streamlit's setComponentValue
            audio.addEventListener('ended', function() {{
                if (hasEnded) return;
                hasEnded = true;

                console.log('Audio ended! Repeat mode:', repeatMode);
                console.log('Sending value to Streamlit via setComponentValue');

                // Send value to Streamlit Python
                window.parent.postMessage({{
                    isStreamlitMessage: true,
                    type: 'streamlit:setComponentValue',
                    value: {{
                        ended: true,
                        repeatMode: repeatMode,
                        timestamp: Date.now()
                    }}
                }}, '*');
            }});

            console.log('Event listeners attached successfully');
        }})();
    </script>
    """

    # Render custom audio player and get return value
    component_value = components.html(html_code, height=80)

    # Get actual duration
    duration = None
    try:
        duration = get_audio_duration_from_bytes(audio_bytes)
        st.caption(f"Duration: {format_time(duration)}")
    except Exception:
        pass

    # Check if component signaled that audio ended
    if component_value and isinstance(component_value, dict) and component_value.get('ended'):
        print(f"[DEBUG] Component signaled audio ended: {component_value}")
        print(f"[DEBUG] Current repeat_mode: {repeat_mode}")

        # Use a session state flag to prevent re-processing
        last_timestamp = st.session_state.get('_last_ended_timestamp', 0)
        current_timestamp = component_value.get('timestamp', 0)

        if current_timestamp != last_timestamp:
            st.session_state['_last_ended_timestamp'] = current_timestamp
            print(f"[DEBUG] Processing audio end, calling _handle_audio_ended")
            _handle_audio_ended(repeat_mode)
        else:
            print(f"[DEBUG] Skipping duplicate audio end event")

    # Download button
    if show_download:
        render_download_button(track, audio_bytes)


def _install_message_listener():
    """
    Install message listener in parent window to handle audio_ended messages from iframe
    This listener will reload the page with auto_advance parameter
    """
    listener_code = """
    <script>
        (function() {
            try {
                // Access parent window
                const targetWindow = window.top || window.parent;

                // Check if listener is already installed in parent window
                if (targetWindow.___streamlit_audio_listener_installed) {
                    console.log('Audio message listener already installed in parent window');
                    return;
                }
                targetWindow.___streamlit_audio_listener_installed = true;

                console.log('Installing audio message listener in parent window');

                // Add event listener to PARENT window
                targetWindow.addEventListener('message', function(event) {
                    console.log('Parent window received message:', event.data);

                    if (event.data && event.data.type === 'audio_ended') {
                        console.log('Audio ended message received in parent, triggering auto-advance');

                        // Add auto_advance parameter and reload page
                        const url = new URL(targetWindow.location.href);
                        url.searchParams.delete('auto_advance');
                        url.searchParams.set('auto_advance', event.data.timestamp.toString());

                        console.log('Reloading parent page:', url.toString());
                        targetWindow.location.href = url.toString();
                    }
                });

                console.log('Audio message listener installed successfully in parent window');
            } catch(e) {
                console.error('Error installing message listener:', e);
            }
        })();
    </script>
    """

    components.html(listener_code, height=0)


def _inject_play_pause_controller(audio_key, is_playing):
    """
    Inject JavaScript to control audio play/pause based on is_playing state and query parameters
    
    Args:
        audio_key: Unique identifier for this audio instance
        is_playing: Whether audio should be playing
    """
    # Check for play/pause command from query parameters
    query_params = st.query_params
    play_pause_param = query_params.get('play_pause')
    last_processed = st.session_state.get('_last_play_pause', '')
    
    # Determine the action to take
    should_play = is_playing
    if play_pause_param and play_pause_param != last_processed:
        should_play = (play_pause_param == 'play')
        st.session_state['_last_play_pause'] = play_pause_param
    
    js_code = f"""
<script>
console.log('Play/Pause controller loading for key: {audio_key}, should_play: {str(should_play).lower()}');
(function() {{
    let checkCount = 0;
    const maxChecks = 20;
    const shouldPlay = {str(should_play).lower()};
    
    function findAndControlAudio() {{
        // Try to find audio in parent window (main Streamlit page)
        let allAudios = [];
        try {{
            if (window.parent && window.parent.document) {{
                allAudios = window.parent.document.querySelectorAll('audio');
                console.log('Found', allAudios.length, 'audio element(s) in parent window');
            }}
        }} catch(e) {{
            console.log('Cannot access parent window:', e);
        }}
        
        // Fallback to current window
        if (allAudios.length === 0) {{
            allAudios = document.querySelectorAll('audio');
            console.log('Found', allAudios.length, 'audio element(s) in current window');
        }}
        
        if (allAudios.length > 0) {{
            const audio = allAudios[allAudios.length - 1]; // Get the most recent audio element
            console.log('Controlling audio element, shouldPlay:', shouldPlay);
            
            if (shouldPlay) {{
                audio.play().catch(e => {{
                    console.log('Error playing audio:', e);
                }});
            }} else {{
                audio.pause();
            }}
            
            return true;
        }}
        
        return false;
    }}
    
    // Check immediately and with retries
    function checkWithRetry() {{
        checkCount++;
        const found = findAndControlAudio();
        
        if (!found && checkCount < maxChecks) {{
            setTimeout(checkWithRetry, 200);
        }} else if (found) {{
            console.log('Audio control applied successfully');
        }}
    }}
    
    // Start checking
    findAndControlAudio();
    setTimeout(checkWithRetry, 100);
    setTimeout(checkWithRetry, 500);
    setTimeout(checkWithRetry, 1000);
    
    console.log('Play/Pause controller initialized for key:', '{audio_key}');
}})();
</script>
"""
    
    components.html(js_code, height=0)


def _inject_audio_end_listener(audio_key, repeat_mode):
    """
    Inject JavaScript to listen for audio ended event and trigger auto-advance
    Uses st.markdown with unsafe_allow_html to inject directly into main page (no iframe)
    
    Args:
        audio_key: Streamlit audio component key
        repeat_mode: Current repeat mode ('none', 'one', 'all')
    """
    # JavaScript code to detect audio end and trigger auto-advance
    # Uses MutationObserver to detect when audio elements are added
    # This script runs in an iframe but accesses parent window to find audio
    js_code = f"""
<script>
console.log('Audio listener script loading for key: {audio_key}');
(function() {{
    const listenerKey = 'audio_listener_{audio_key}';
    const processedAudios = new Set();
    let checkCount = 0;
    const maxChecks = 20; // Check up to 20 times
    
    function attachAudioListener(audioElement) {{
        // Skip if already processed
        if (processedAudios.has(audioElement)) {{
            return;
        }}
        
        processedAudios.add(audioElement);
        
        // Add ended event listener directly to the element (don't clone)
        // Use a unique identifier to prevent duplicate listeners
        const listenerId = 'autoAdvanceListener_' + Date.now();
        if (audioElement.dataset.listenerId) {{
            // Already has a listener, skip
            return;
        }}
        
        audioElement.dataset.listenerId = listenerId;
        
        let hasEnded = false;
        
        // Method 1: Listen for 'ended' event
        audioElement.addEventListener('ended', function(event) {{
            if (hasEnded) return; // Prevent duplicate triggers
            hasEnded = true;
            console.log('Audio playback ended (event) - triggering auto-advance', event);
            triggerAutoAdvance();
        }}, {{ once: false }});
        
        // Method 2: Monitor timeupdate to detect when audio finishes
        let lastCheckTime = 0;
        audioElement.addEventListener('timeupdate', function() {{
            if (hasEnded) return;
            
            const currentTime = audioElement.currentTime;
            const duration = audioElement.duration;
            const isPlaying = !audioElement.paused;
            
            // Check if audio has finished (within 0.1 seconds of end)
            if (duration && duration > 0 && currentTime >= duration - 0.1 && isPlaying) {{
                if (!hasEnded) {{
                    hasEnded = true;
                    console.log('Audio playback ended (timeupdate) - triggering auto-advance');
                    console.log('Current time:', currentTime, 'Duration:', duration);
                    triggerAutoAdvance();
                }}
            }}
            
            // Log progress every second
            if (Math.floor(currentTime) !== Math.floor(lastCheckTime)) {{
                console.log('Audio progress:', currentTime.toFixed(2), '/', duration ? duration.toFixed(2) : 'unknown');
            }}
            lastCheckTime = currentTime;
        }});
        
        // Method 3: Fallback - check periodically if ended event doesn't fire
        let checkInterval = setInterval(function() {{
            if (hasEnded) {{
                clearInterval(checkInterval);
                return;
            }}
            
            const duration = audioElement.duration;
            const currentTime = audioElement.currentTime;
            
            if (duration && duration > 0 && currentTime >= duration - 0.05 && !audioElement.paused) {{
                hasEnded = true;
                clearInterval(checkInterval);
                console.log('Audio playback ended (interval check) - triggering auto-advance');
                triggerAutoAdvance();
            }}
        }}, 100); // Check every 100ms
        
        function triggerAutoAdvance() {{
            // Trigger Streamlit rerun via URL parameter
            try {{
                let targetWindow = window;
                try {{
                    // Try to access parent window (for iframe)
                    if (window.parent && window.parent !== window && window.parent.location) {{
                        targetWindow = window.parent;
                        console.log('Using parent window for URL change');
                    }} else {{
                        console.log('Using current window for URL change');
                    }}
                }} catch(e) {{
                    // If we can't access parent, use current window
                    console.log('Cannot access parent window, using current window:', e);
                }}
                
                const currentUrl = targetWindow.location.href;
                console.log('Current URL:', currentUrl);
                const url = new URL(currentUrl);
                // Remove existing auto_advance param
                url.searchParams.delete('auto_advance');
                // Add new one with timestamp to force reload
                url.searchParams.set('auto_advance', Date.now().toString());
                const newUrl = url.toString();
                console.log('Reloading with URL:', newUrl);
                targetWindow.location.href = newUrl;
            }} catch(e) {{
                console.log('Error triggering reload:', e);
                console.error(e);
            }}
        }}
        
        console.log('Audio end listener attached successfully to:', audioElement);
        console.log('Audio element details:', {{
            src: audioElement.src ? audioElement.src.substring(0, 100) : 'no src',
            duration: audioElement.duration,
            paused: audioElement.paused,
            readyState: audioElement.readyState
        }});
        
        // Verify the listener is actually attached
        const listeners = getEventListeners ? getEventListeners(audioElement) : 'getEventListeners not available';
        console.log('Event listeners on audio element:', listeners);
    }}
    
    function findAndAttachToAudios() {{
        // Find audio elements in current window and parent window
        let allAudios = [];
        
        // First try current window
        try {{
            allAudios = Array.from(document.querySelectorAll('audio'));
            console.log('Found', allAudios.length, 'audio element(s) in current window');
        }} catch(e) {{
            console.log('Error querying current window:', e);
        }}
        
        // Also try parent window (for iframe cases)
        try {{
            if (window.parent && window.parent !== window && window.parent.document) {{
                const parentAudios = Array.from(window.parent.document.querySelectorAll('audio'));
                console.log('Found', parentAudios.length, 'audio element(s) in parent window');
                // Merge with current window audios, avoiding duplicates
                parentAudios.forEach(audio => {{
                    if (!allAudios.includes(audio)) {{
                        allAudios.push(audio);
                    }}
                }});
            }}
        }} catch(e) {{
            console.log('Cannot access parent window:', e);
        }}
        
        let attachedCount = 0;
        allAudios.forEach(audio => {{
            if (!processedAudios.has(audio)) {{
                attachAudioListener(audio);
                attachedCount++;
                console.log('Attached listener to audio element, src:', audio.src ? audio.src.substring(0, 50) : 'no src');
            }}
        }});
        
        return allAudios.length;
    }}
    
    // Use MutationObserver to watch for new audio elements
    function setupObserver() {{
        let targetBodies = [document.body];
        
        // Also observe parent window body if accessible
        try {{
            if (window.parent && window.parent !== window && window.parent.document && window.parent.document.body) {{
                targetBodies.push(window.parent.document.body);
                console.log('Will observe both current and parent window bodies');
            }}
        }} catch(e) {{
            console.log('Cannot access parent body for observer:', e);
        }}
        
        targetBodies.forEach(targetBody => {{
            if (targetBody) {{
                const observer = new MutationObserver(function(mutations) {{
                    let shouldCheck = false;
                    mutations.forEach(function(mutation) {{
                        if (mutation.addedNodes.length > 0) {{
                            mutation.addedNodes.forEach(function(node) {{
                                if (node.nodeType === 1) {{ // Element node
                                    if (node.tagName === 'AUDIO' || (node.querySelector && node.querySelector('audio'))) {{
                                        shouldCheck = true;
                                        console.log('New audio element detected in DOM');
                                    }}
                                }}
                            }});
                        }}
                    }});
                    
                    if (shouldCheck) {{
                        console.log('Mutation detected, checking for new audio elements...');
                        setTimeout(findAndAttachToAudios, 100);
                    }}
                }});
                
                // Start observing
                observer.observe(targetBody, {{
                    childList: true,
                    subtree: true
                }});
                console.log('MutationObserver set up for body');
            }}
        }});
    }}
    
    setupObserver();
    
    // Also check immediately and with delays
    function checkWithRetry() {{
        checkCount++;
        const found = findAndAttachToAudios();
        
        if (found === 0 && checkCount < maxChecks) {{
            // No audio found yet, keep trying
            setTimeout(checkWithRetry, 500);
        }} else if (found > 0) {{
            console.log('Found', found, 'audio element(s)');
        }}
    }}
    
    findAndAttachToAudios();
    setTimeout(checkWithRetry, 500);
    setTimeout(checkWithRetry, 1500);
    setTimeout(checkWithRetry, 3000);
    
    console.log('Audio observer initialized for key:', '{audio_key}');
}})();
</script>
"""
    
    # Inject the JavaScript using components.html
    components.html(js_code, height=0)
    
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

    print(f"[DEBUG] _handle_audio_ended called: current_track={current_track}, total={total_tracks}, mode={repeat_mode}")

    # Use handle_track_end to determine next track (same module, no import needed)
    next_track, should_play = handle_track_end(current_track, total_tracks, repeat_mode)

    print(f"[DEBUG] handle_track_end returned: next_track={next_track}, should_play={should_play}")

    if should_play:
        # Update track and force audio refresh
        # For Repeat One mode, next_track will be the same as current_track
        st.session_state.current_track = next_track
        st.session_state.play_count = st.session_state.get('play_count', 0) + 1
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
