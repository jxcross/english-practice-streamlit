"""
Streamlit English Practice Player
Main application file
"""
import streamlit as st
from modules import ui_components
from modules.tts_engine import TTSEngine
from modules.audio_player import render_audio_player
from modules.cache_inspector import render_cache_inspector


# Page configuration
st.set_page_config(
    page_title="English Practice Player",
    page_icon="assets/logo-128.png",  # Using new professional logo
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state with default values"""
    defaults = {
        'tracks': [],
        'current_track': 0,
        'is_playing': True,  # Default to True for auto-play
        'playback_speed': 1.0,
        'repeat_mode': 'none',
        'selected_voice': 'en-US-Standard-F',
        'api_key': None,
        'current_screen': 'upload',  # 'upload' or 'player'
        'auto_play': False,
        'audio_finished': False,
        'play_count': 0,  # Track number of plays to force audio refresh
        'session_api_calls': 0,  # Track API calls in this session
        'session_cache_hits': 0,  # Track cache hits in this session
        'batch_load_summary': None,  # Summary of last batch load
        'loaded_audio_cache': None,  # Cached audio bytes list
        'loaded_audio_cache_key': None  # Key to detect when to reload audio
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _handle_auto_play_next():
    """Handle auto-play next track based on repeat mode"""
    from modules.audio_player import handle_track_end
    
    total_tracks = len(st.session_state.tracks)
    current_track = st.session_state.current_track
    repeat_mode = st.session_state.get('repeat_mode', 'none')

    # Use handle_track_end for consistent logic
    next_track, should_play = handle_track_end(current_track, total_tracks, repeat_mode)
    
    if should_play:
        # Increment play count to force audio refresh (even for Repeat One)
        st.session_state.play_count += 1
        st.session_state.current_track = next_track


def _generate_track_audio_cached(text, voice, api_key):
    """
    Wrapper for audio generation with session-level statistics tracking
    """
    tts_engine = TTSEngine(api_key=api_key)
    audio_bytes, duration, cache_hit = tts_engine.generate_audio(text, voice)

    # Update session-level stats (more reliable than cache manager stats)
    if cache_hit:
        st.session_state.session_cache_hits = st.session_state.get('session_cache_hits', 0) + 1
    else:
        st.session_state.session_api_calls = st.session_state.get('session_api_calls', 0) + 1

    return audio_bytes, duration, cache_hit


def render_upload_screen():
    """Render upload/playlist selection screen"""
    # Header with logo
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("assets/logo-256.png", width=120)
    with col2:
        st.title("English Practice Player")
        st.markdown("*영어 학습 플레이어*")

    # Show "Go to Player" button if tracks are loaded
    if st.session_state.get('tracks'):
        track_count = len(st.session_state.tracks)
        st.info(f"📀 {track_count} tracks loaded")
        if st.button("▶️ Go to Player", key="go_to_player_btn", type="primary"):
            st.session_state.current_screen = 'player'
            st.rerun()

    st.markdown("---")

    # Input tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 CSV Upload",
        "📝 Text Paste",
        "📋 Saved Playlists",
        "🎯 Sample Data",
        "🔍 Cache Inspector"
    ])

    with tab1:
        ui_components.render_csv_upload()

    with tab2:
        ui_components.render_text_paste()

    with tab3:
        ui_components.render_saved_playlists()

    with tab4:
        ui_components.render_sample_data()

    with tab5:
        # Cache Inspector tab (API key not required for viewing cache)
        tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))
        render_cache_inspector(tts_engine)


def render_player_screen():
    """Render player screen with controls and audio"""
    # Header with logo and back button
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.image("assets/logo-128.png", width=60)
    with col2:
        st.markdown("### English Practice Player")
    with col3:
        if st.button("← Back", key="back_btn"):
            st.session_state.current_screen = 'upload'
            st.session_state.is_playing = False
            st.rerun()

    st.markdown("---")

    # Check if we have tracks
    if not st.session_state.tracks:
        st.warning("No tracks loaded. Please go back and load a playlist.")
        return

    # Initialize TTS engine (needed for actions)
    tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))

    # Track info
    current_idx = st.session_state.current_track
    total = len(st.session_state.tracks)

    #st.markdown(f"### Track {current_idx + 1} of {total}")

    # Get current track
    #track = st.session_state.tracks[current_idx]

    # # Display text
    # st.markdown(f"## {track['english']}")
    # st.markdown(f"*{track['korean']}*")

    # st.markdown("---")

    # Generate and play audio (works with or without API key)
    try:
        selected_voice = st.session_state.get('selected_voice', 'en-US-Standard-F')

        # Generate audio for all tracks (or next 20 tracks for performance)
        total_tracks = len(st.session_state.tracks)
        max_tracks_to_load = min(total_tracks, 20)  # Load up to 20 tracks at once
        tracks_to_load = st.session_state.tracks[:max_tracks_to_load]

        # Create cache key to detect if we need to reload audio
        # Key format: (track_texts_hash, voice, api_key_prefix)
        import hashlib
        tracks_text = '|'.join([t['english'] for t in tracks_to_load])
        tracks_hash = hashlib.md5(tracks_text.encode()).hexdigest()
        api_key_part = (st.session_state.get('api_key') or 'none')[:10]
        current_cache_key = f"{tracks_hash}_{selected_voice}_{api_key_part}"

        # Check if we can reuse cached audio from session state
        if (st.session_state.loaded_audio_cache is not None and
            st.session_state.loaded_audio_cache_key == current_cache_key):
            # Reuse cached audio - no need to reload!
            audio_bytes_list = st.session_state.loaded_audio_cache
            st.info("♻️ Using previously loaded audio (no API key needed)")
        else:
            # Need to load audio - try cache first, then generate
            # Initialize TTS engine (API key optional for cache access)
            tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))

            audio_bytes_list = []
            cache_hits_list = []
            all_cached = True

            with st.spinner(f"Loading audio for {max_tracks_to_load} tracks..."):
                for i, t in enumerate(tracks_to_load):
                    try:
                        # Try to load from cache or generate
                        audio_bytes, duration, cache_hit = _generate_track_audio_cached(
                            text=t['english'],
                            voice=selected_voice,
                            api_key=st.session_state.get('api_key')
                        )
                        audio_bytes_list.append(audio_bytes)
                        cache_hits_list.append(cache_hit)
                        if not cache_hit:
                            all_cached = False

                        # Show cache status for current track only
                        if i == current_idx and cache_hit:
                            st.sidebar.success("✅ Loaded from cache")

                    except Exception as e:
                        error_msg = str(e)
                        if "No API key" in error_msg or "API key required" in error_msg:
                            # API key missing and cache miss
                            st.error(f"⚠️ No cached audio for track {i+1}: \"{t['english'][:50]}...\"")
                            st.error("Please enter your Google Cloud TTS API key in the sidebar to generate new audio.")
                            st.info("💡 Tip: Previously generated tracks are cached and can be played without an API key.")
                            return
                        else:
                            st.error(f"Error loading track {i+1}: {error_msg}")
                            return

                # Successfully loaded all tracks
                cache_hits_count = sum(1 for hit in cache_hits_list if hit)
                cache_misses_count = len(cache_hits_list) - cache_hits_count

                # Save to session cache
                st.session_state.loaded_audio_cache = audio_bytes_list
                st.session_state.loaded_audio_cache_key = current_cache_key

                # Save batch summary
                st.session_state.batch_load_summary = {
                    'total': len(cache_hits_list),
                    'cache_hits': cache_hits_count,
                    'api_calls': cache_misses_count
                }

                # Show summary
                if all_cached:
                    st.success(f"✅ Loaded {len(cache_hits_list)} tracks from cache (no API key needed)")
                else:
                    st.info(f"📊 Loaded {len(cache_hits_list)} tracks: {cache_hits_count} from cache, {cache_misses_count} from API")

        # Render audio player (always, regardless of API key)
        render_audio_player(
            audio_bytes_list=audio_bytes_list,
            tracks=tracks_to_load,
            current_track_idx=current_idx,
            show_download=True
        )

        # Display batch load summary
        if st.session_state.batch_load_summary:
            summary = st.session_state.batch_load_summary
            if summary['api_calls'] > 0:
                st.caption(f"💰 {summary['api_calls']} API calls made this batch")

        # Auto-play info (appears when auto-play is enabled)
        if st.session_state.get('auto_play', False):
            st.markdown("---")
            repeat_mode = st.session_state.get('repeat_mode', 'none')
            mode_desc = {
                'none': '순차 재생 (마지막 트랙에서 정지)',
                'one': '현재 트랙 반복',
                'all': '전체 플레이리스트 반복'
            }
            st.info(f"🔄 Auto-Play 활성화: {mode_desc.get(repeat_mode, '')} - 오디오 재생이 끝나면 자동으로 다음 트랙으로 진행됩니다.")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        if "API key" in str(e):
            st.info("💡 Please enter your Google Cloud TTS API key in the sidebar.")

    # # Playback controls
    # st.markdown("---")
    # ui_components.render_playback_controls()

    # # Repeat mode
    # st.markdown("---")
    # ui_components.render_repeat_mode_simple()

    # Actions (moved from right sidebar to main screen bottom)
    st.markdown("---")
    st.markdown("### Actions")
    ui_components.render_playlist_actions(tts_engine)


def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()

    # Render API key input in sidebar
    ui_components.render_api_key_input()

    st.sidebar.markdown("---")

    # Voice selection (only if API key present - requires API call)
    if st.session_state.get('api_key'):
        tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))
        ui_components.render_voice_selection(tts_engine)
        st.sidebar.markdown("---")

    # Cache stats (accessible without API key)
    st.sidebar.markdown("### 💾 Cache Stats")

    # Initialize TTS engine for cache access (no API key needed)
    tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))
    stats = tts_engine.get_cache_stats()

    st.sidebar.metric("Cached Items", stats['items'])
    st.sidebar.metric("Cache Size", f"{stats['size_mb']:.1f} MB / {stats['max_size_mb']} MB")
    st.sidebar.progress(stats['usage_percent'] / 100)

    # Session statistics (primary source of truth)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**This Session**")

    session_api_calls = st.session_state.get('session_api_calls', 0)
    session_cache_hits = st.session_state.get('session_cache_hits', 0)
    session_total = session_api_calls + session_cache_hits

    if session_total > 0:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Cache Hits", session_cache_hits)
        with col2:
            st.metric("API Calls", session_api_calls)

        # Calculate and display session hit rate
        session_hit_rate = (session_cache_hits / session_total) * 100
        st.sidebar.metric("Hit Rate", f"{session_hit_rate:.1f}%")
        st.sidebar.caption(f"💰 {session_hit_rate:.1f}% saved this session")
    else:
        st.sidebar.caption("Load a playlist to see statistics")

        



    # Main routing
    if st.session_state.current_screen == 'upload':
        render_upload_screen()
    else:
        render_player_screen()


if __name__ == "__main__":
    main()
