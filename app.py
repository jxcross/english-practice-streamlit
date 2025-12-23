"""
Streamlit English Practice Player
Main application file
"""
import streamlit as st
from modules import ui_components
from modules.tts_engine import TTSEngine
from modules.audio_player import render_audio_player


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
        'is_playing': False,
        'playback_speed': 1.0,
        'repeat_mode': 'none',
        'selected_voice': 'en-US-Standard-F',
        'api_key': None,
        'current_screen': 'upload',  # 'upload' or 'player'
        'auto_play': False,
        'audio_finished': False,
        'play_count': 0  # Track number of plays to force audio refresh
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


def render_upload_screen():
    """Render upload/playlist selection screen"""
    st.title("🎵 English Practice Player")
    st.markdown("*영어 학습 플레이어*")

    st.markdown("---")

    # Input tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 CSV Upload",
        "📝 Text Paste",
        "📋 Saved Playlists",
        "🎯 Sample Data"
    ])

    with tab1:
        ui_components.render_csv_upload()

    with tab2:
        ui_components.render_text_paste()

    with tab3:
        ui_components.render_saved_playlists()

    with tab4:
        ui_components.render_sample_data()


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

    # Initialize TTS engine
    tts_engine = TTSEngine(api_key=st.session_state.get('api_key'))

    # Main layout
    col1, col2 = st.columns([3, 1])

    with col1:
        # Track info
        current_idx = st.session_state.current_track
        total = len(st.session_state.tracks)

        st.markdown(f"### Track {current_idx + 1} of {total}")

        # Get current track
        track = st.session_state.tracks[current_idx]

        # Display text
        st.markdown(f"## {track['english']}")
        st.markdown(f"*{track['korean']}*")

        st.markdown("---")

        # Generate and play audio
        if st.session_state.get('api_key'):
            try:
                with st.spinner("Generating audio..."):
                    selected_voice = st.session_state.get('selected_voice', 'en-US-Standard-F')

                    audio_bytes, duration, cache_hit = tts_engine.generate_audio(
                        text=track['english'],
                        voice=selected_voice
                    )

                    if cache_hit:
                        st.success("✅ Loaded from cache")

                    # Render audio player with download button
                    render_audio_player(audio_bytes, track, show_download=True)

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

        # Playback controls
        st.markdown("---")
        ui_components.render_playback_controls()

        # Repeat mode
        ui_components.render_repeat_mode()

    with col2:
        # Playlist actions
        st.markdown("### Actions")
        ui_components.render_playlist_actions(tts_engine)

        st.markdown("---")

        # Voice selection
        if st.session_state.get('api_key'):
            ui_components.render_voice_selection(tts_engine)

            st.markdown("---")

            # Cache stats
            st.markdown("### 💾 Cache Stats")
            stats = tts_engine.get_cache_stats()
            st.metric("Cached Items", stats['items'])
            st.metric("Cache Size", f"{stats['size_mb']:.1f} MB / {stats['max_size_mb']} MB")
            st.progress(stats['usage_percent'] / 100)

        st.markdown("---")

        # Playlist view
        ui_components.render_playlist_view()


def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()

    # Render API key input in sidebar
    ui_components.render_api_key_input()

    st.sidebar.markdown("---")

    # Sidebar info
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info(
        "English Practice Player allows you to create playlists of "
        "English-Korean sentence pairs and practice listening with "
        "high-quality Google Cloud Text-to-Speech."
    )

    st.sidebar.markdown("### 📖 How to Use")
    st.sidebar.markdown("""
1. **Get API Key**: Obtain a Google Cloud TTS API key
2. **Upload Data**: CSV file or paste text
3. **Select Voice**: Choose from available voices
4. **Play & Practice**: Listen and download MP3s
""")

    # Main routing
    if st.session_state.current_screen == 'upload':
        render_upload_screen()
    else:
        render_player_screen()


if __name__ == "__main__":
    main()
