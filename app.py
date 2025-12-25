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
    page_icon="🎵",
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
        'batch_load_summary': None  # Summary of last batch load
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
    st.title("🎵 English Practice Player")
    st.markdown("*영어 학습 플레이어*")

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
        # Cache Inspector tab
        if st.session_state.get('api_key'):
            tts_engine = TTSEngine(api_key=st.session_state.api_key)
            render_cache_inspector(tts_engine)
        else:
            st.warning("⚠️ Please enter your Google Cloud TTS API key in the sidebar to view cache")


def render_player_screen():
    """Render player screen with controls and audio"""
    # Back button
    if st.button("← Back to Upload", key="back_btn"):
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

    # Generate and play audio
    if st.session_state.get('api_key'):
        try:
            selected_voice = st.session_state.get('selected_voice', 'en-US-Standard-F')
            
            # Generate audio for all tracks (or next 20 tracks for performance)
            total_tracks = len(st.session_state.tracks)
            max_tracks_to_load = min(total_tracks, 20)  # Load up to 20 tracks at once
            
            with st.spinner(f"Generating audio for {max_tracks_to_load} tracks..."):
                audio_bytes_list = []
                cache_hits_list = []
                tracks_to_load = st.session_state.tracks[:max_tracks_to_load]

                for i, t in enumerate(tracks_to_load):
                    try:
                        # Use Streamlit-cached wrapper for better performance
                        audio_bytes, duration, cache_hit = _generate_track_audio_cached(
                            text=t['english'],
                            voice=selected_voice,
                            api_key=st.session_state.api_key
                        )
                        audio_bytes_list.append(audio_bytes)
                        cache_hits_list.append(cache_hit)

                        # Show cache status for current track only
                        if i == current_idx and cache_hit:
                            st.sidebar.success("✅ Loaded from cache")
                    except Exception as e:
                        st.sidebar.warning(f"Error generating audio for track {i+1}: {str(e)}")
                        audio_bytes_list.append(None)
                        cache_hits_list.append(False)

                # Calculate batch statistics (session stats already updated in _generate_track_audio_cached)
                cache_hits_count = sum(1 for hit in cache_hits_list if hit)
                cache_misses_count = len(cache_hits_list) - cache_hits_count

                # Save batch summary (don't update session counters here - already done in wrapper)
                st.session_state.batch_load_summary = {
                    'total': len(cache_hits_list),
                    'cache_hits': cache_hits_count,
                    'api_calls': cache_misses_count
                }

                # Render audio player with all tracks data
                render_audio_player(
                    audio_bytes_list=audio_bytes_list,
                    tracks=tracks_to_load,
                    current_track_idx=current_idx,
                    show_download=True
                )

                # Display batch load summary
                if st.session_state.batch_load_summary:
                    summary = st.session_state.batch_load_summary
                    st.info(f"📊 Loaded {summary['total']} tracks: "
                            f"{summary['cache_hits']} from cache, "
                            f"{summary['api_calls']} from API")

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
            st.error(f"Error generating audio: {str(e)}")
            st.info("Please check your API key and try again")

    else:
        st.warning("⚠️ Please enter your Google Cloud TTS API key in the sidebar to generate audio")

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

    # Cache stats (moved from right sidebar)
    if st.session_state.get('api_key'):
        tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))
        
        # Voice selection (moved to bottom of sidebar)
        ui_components.render_voice_selection(tts_engine)

        st.sidebar.markdown("---")
        
        st.sidebar.markdown("### 💾 Cache Stats")
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

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Cache Hits", session_cache_hits)
        with col2:
            st.metric("API Calls", session_api_calls)

        # Calculate and display session hit rate
        if session_total > 0:
            session_hit_rate = (session_cache_hits / session_total) * 100
            st.sidebar.metric("Hit Rate", f"{session_hit_rate:.1f}%")
            st.sidebar.caption(f"💰 {session_hit_rate:.1f}% saved this session")
        else:
            st.sidebar.metric("Hit Rate", "0.0%")
            st.sidebar.caption("Load a playlist to see cache statistics")

        



    # Main routing
    if st.session_state.current_screen == 'upload':
        render_upload_screen()
    else:
        render_player_screen()


if __name__ == "__main__":
    main()
