"""
UI Components for Streamlit English Practice Player
Reusable widgets for upload, playback controls, playlists, etc.
"""
import streamlit as st
import json
from datetime import datetime
from modules.csv_parser import parse_csv_file, parse_text_input
from modules.storage import StorageManager
from modules.audio_player import create_playlist_zip
from utils.security import validate_api_key, mask_api_key


def render_csv_upload():
    """Render CSV file upload tab"""
    st.markdown("### 📂 Upload CSV File")
    st.markdown("CSV file must have 'english' and 'korean' columns")

    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key='csv_uploader')

    if uploaded_file is not None:
        tracks, error = parse_csv_file(uploaded_file)

        if error:
            st.error(error)
        else:
            st.success(f"✅ Loaded {len(tracks)} tracks")

            # Preview
            st.markdown("**Preview:**")
            for i, track in enumerate(tracks[:3]):
                st.text(f"{i+1}. {track['english']}")
                st.caption(f"   {track['korean']}")

            if len(tracks) > 3:
                st.caption(f"   ... and {len(tracks) - 3} more")

            # Load button
            if st.button("Load Playlist", key='load_csv'):
                st.session_state.tracks = tracks
                st.session_state.current_track = 0
                st.session_state.current_screen = 'player'
                st.rerun()


def render_text_paste():
    """Render text paste tab"""
    st.markdown("### 📝 Paste Text")
    st.markdown("**Supported formats:**")
    st.markdown("1. **CSV**: `english,korean` (with header)")
    st.markdown("2. **Line-by-line**: Alternating English and Korean lines")

    text_input = st.text_area(
        "Paste your text here",
        height=200,
        placeholder="Format 1:\nenglish,korean\nHello,안녕하세요\n\nFormat 2:\nHello\n안녕하세요\nGoodbye\n안녕히 가세요",
        key='text_input'
    )

    if st.button("Parse Text", key='parse_text'):
        if text_input:
            tracks, error = parse_text_input(text_input)

            if error:
                st.error(error)
            else:
                st.success(f"✅ Parsed {len(tracks)} tracks")

                # Preview
                st.markdown("**Preview:**")
                for i, track in enumerate(tracks[:3]):
                    st.text(f"{i+1}. {track['english']}")
                    st.caption(f"   {track['korean']}")

                if len(tracks) > 3:
                    st.caption(f"   ... and {len(tracks) - 3} more")

                # Load button
                if st.button("Load Playlist", key='load_text'):
                    st.session_state.tracks = tracks
                    st.session_state.current_track = 0
                    st.session_state.current_screen = 'player'
                    st.rerun()
        else:
            st.warning("Please paste some text first")


def render_saved_playlists():
    """Render saved playlists tab"""
    st.markdown("### 📋 Saved Playlists")

    storage = StorageManager()
    playlists = storage.list_playlists()

    if not playlists:
        st.info("No saved playlists yet. Create one by saving your current playlist in the player screen.")
        return

    for playlist in playlists:
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"**{playlist['name']}**")
            st.caption(f"{playlist['track_count']} tracks • Created {playlist['created_at'][:10]}")

        with col2:
            if st.button("Load", key=f"load_{playlist['name']}"):
                tracks = storage.load_playlist(playlist['name'])
                if tracks:
                    st.session_state.tracks = tracks
                    st.session_state.current_track = 0
                    st.session_state.current_screen = 'player'
                    st.rerun()

        with col3:
            if st.button("🗑️", key=f"delete_{playlist['name']}"):
                if storage.delete_playlist(playlist['name']):
                    st.success(f"Deleted '{playlist['name']}'")
                    st.rerun()


def render_sample_data():
    """Render sample data tab"""
    st.markdown("### 🎯 Sample Data")
    st.markdown("Load sample English-Korean conversation pairs for testing")

    try:
        with open('data/sample_data.json', 'r', encoding='utf-8') as f:
            sample_tracks = json.load(f)

        st.info(f"📊 {len(sample_tracks)} sample tracks available")

        # Preview
        st.markdown("**Preview:**")
        for i, track in enumerate(sample_tracks[:2]):
            st.text(f"{i+1}. {track['english']}")
            st.caption(f"   {track['korean']}")

        if st.button("Load Sample Data", key='load_sample'):
            st.session_state.tracks = sample_tracks
            st.session_state.current_track = 0
            st.session_state.current_screen = 'player'
            st.rerun()

    except FileNotFoundError:
        st.error("Sample data file not found")
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")


def render_api_key_input():
    """Render API key input in sidebar"""
    st.sidebar.markdown("### 🔑 Google Cloud TTS API Key")

    # Check current status
    has_key = st.session_state.get('api_key') is not None

    if has_key:
        st.sidebar.success(f"✅ API Key: {mask_api_key(st.session_state.api_key)}")

        if st.sidebar.button("Clear API Key"):
            st.session_state.api_key = None
            st.rerun()

    else:
        st.sidebar.info("Enter your Google Cloud TTS API key to enable high-quality audio generation")

        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            placeholder="AIzaSy...",
            key='api_key_input'
        )

        if st.sidebar.button("Save API Key"):
            if validate_api_key(api_key):
                st.session_state.api_key = api_key
                st.sidebar.success("✅ API Key saved!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid API key format. Must start with 'AIzaSy' and be at least 39 characters.")

        st.sidebar.caption("Your API key is stored only in your session and never persisted to disk.")


def render_playback_controls():
    """Render playback control buttons with auto-advance support"""
    st.markdown("### 🎮 Playback Controls")

    col1, col2, col3, col4, col5 = st.columns(5)

    total_tracks = len(st.session_state.tracks)

    with col1:
        if st.button("⏮ First", disabled=st.session_state.current_track == 0):
            st.session_state.current_track = 0
            st.session_state.play_count = st.session_state.get('play_count', 0) + 1
            st.rerun()

    with col2:
        if st.button("◀ Prev", disabled=st.session_state.current_track == 0):
            st.session_state.current_track -= 1
            st.session_state.play_count = st.session_state.get('play_count', 0) + 1
            st.rerun()

    with col3:
        play_label = "⏸ Pause" if st.session_state.get('is_playing', False) else "▶️ Play"
        if st.button(play_label, key="play_pause_btn"):
            new_state = not st.session_state.get('is_playing', False)
            st.session_state.is_playing = new_state
            # Use query parameter to trigger JavaScript control
            # Convert query_params to dict, modify, then update
            params = dict(st.query_params)
            params['play_pause'] = 'play' if new_state else 'pause'
            params['_t'] = str(int(st.session_state.get('play_count', 0) * 1000))
            st.query_params.update(params)
            st.rerun()

    with col4:
        # Next button handles repeat mode
        # Disable only if 'none' mode and at last track
        repeat_mode = st.session_state.get('repeat_mode', 'none')
        next_disabled = (repeat_mode == 'none' and st.session_state.current_track >= total_tracks - 1)
        if st.button("▶ Next", disabled=next_disabled):
            _handle_next_track()
            st.rerun()

    with col5:
        if st.button("⏭ Last", disabled=st.session_state.current_track == total_tracks - 1):
            st.session_state.current_track = total_tracks - 1
            st.session_state.play_count = st.session_state.get('play_count', 0) + 1
            st.rerun()


def _handle_next_track():
    """Handle next track with repeat mode logic"""
    from modules.audio_player import handle_track_end
    
    total_tracks = len(st.session_state.tracks)
    current_track = st.session_state.current_track
    repeat_mode = st.session_state.get('repeat_mode', 'none')

    # Use handle_track_end for consistent logic
    next_track, should_play = handle_track_end(current_track, total_tracks, repeat_mode)
    
    if should_play:
        # Increment play count to force audio refresh
        st.session_state.play_count = st.session_state.get('play_count', 0) + 1
        # Update track (for Repeat One mode, next_track will be the same as current_track)
        st.session_state.current_track = next_track


def render_voice_selection(tts_engine):
    """Render voice selection dropdown in sidebar"""
    st.sidebar.markdown("### 🎤 Voice Selection")

    voices = tts_engine.get_available_voices()

    if not voices:
        st.sidebar.warning("No voices available. Please check your API key.")
        return

    # Create voice options
    voice_options = {voice['description']: voice['name'] for voice in voices}

    # Get current selection
    current_voice = st.session_state.get('selected_voice', 'en-US-Standard-F')

    # Find current description
    current_desc = None
    for desc, name in voice_options.items():
        if name == current_voice:
            current_desc = desc
            break

    # Voice selector
    selected_desc = st.sidebar.selectbox(
        "Select Voice",
        options=list(voice_options.keys()),
        index=list(voice_options.values()).index(current_voice) if current_voice in voice_options.values() else 0,
        key='voice_selector'
    )

    # Update session state if changed
    new_voice = voice_options[selected_desc]
    if new_voice != current_voice:
        st.session_state.selected_voice = new_voice


def render_repeat_mode():
    """Render repeat mode selector with auto-play toggle"""
    st.markdown("### 🔁 Repeat & Auto-Play")

    # Auto-play toggle
    auto_play = st.toggle(
        "🔄 Auto-Play Next Track",
        value=st.session_state.get('auto_play', False),
        help="Automatically play next track based on repeat mode",
        key='auto_play_toggle'
    )
    st.session_state.auto_play = auto_play

    st.markdown("---")

    # Repeat mode selector
    repeat_options = {
        'None': 'none',
        'Repeat One': 'one',
        'Repeat All': 'all'
    }

    current_mode = st.session_state.get('repeat_mode', 'none')

    # Find current label
    current_label = None
    for label, mode in repeat_options.items():
        if mode == current_mode:
            current_label = label
            break

    selected_label = st.radio(
        "Repeat Mode",
        options=list(repeat_options.keys()),
        index=list(repeat_options.values()).index(current_mode) if current_mode in repeat_options.values() else 0,
        horizontal=True,
        key='repeat_selector'
    )

    # Update session state if changed
    new_mode = repeat_options[selected_label]
    if new_mode != current_mode:
        st.session_state.repeat_mode = new_mode

        # Repeat One/All이면 연속재생을 위해 auto_play 켬
        if new_mode in ['one', 'all']:
            st.session_state.auto_play = True
        else:
            st.session_state.auto_play = False

        # st.audio는 key가 없으니, play_count로 새 오디오 렌더 유도
        st.session_state.play_count = st.session_state.get('play_count', 0) + 1

        st.rerun()

    # Show mode description
    mode_descriptions = {
        'none': '순차 재생 (마지막 트랙에서 정지)',
        'one': '현재 트랙 반복',
        'all': '전체 플레이리스트 반복'
    }
    st.caption(f"ℹ️ {mode_descriptions.get(new_mode, '')}")


def render_repeat_mode_simple():
    """Render simple repeat mode selector (none, one, all)"""
    st.markdown("### 🔁 Repeat Mode")

    # Repeat mode selector
    repeat_options = {
        'None': 'none',
        'Repeat One': 'one',
        'Repeat All': 'all'
    }

    current_mode = st.session_state.get('repeat_mode', 'none')

    # Find current index
    current_index = 0
    if current_mode in repeat_options.values():
        current_index = list(repeat_options.values()).index(current_mode)

    selected_label = st.radio(
        "Repeat Mode",
        options=list(repeat_options.keys()),
        index=current_index,
        horizontal=True,
        key='repeat_selector_simple'
    )

    # Update session state if changed
    new_mode = repeat_options[selected_label]
    if new_mode != current_mode:
        st.session_state.repeat_mode = new_mode
        # Enable auto-play for Repeat One and Repeat All modes
        if new_mode in ['one', 'all']:
            st.session_state.auto_play = True
            # If switching to Repeat All, start from the first track
            if new_mode == 'all':
                st.session_state.current_track = 0
        else:
            # For 'none' mode, disable auto-play
            st.session_state.auto_play = False
        
        # Force rerun to apply the change immediately (JS will pick up new repeat mode)
        st.rerun()

    # Show mode description
    mode_descriptions = {
        'none': '순차 재생 (마지막 트랙에서 정지)',
        'one': '현재 트랙 반복',
        'all': '전체 플레이리스트 반복'
    }
    st.caption(f"ℹ️ {mode_descriptions.get(new_mode, '')}")


def render_playlist_actions(tts_engine):
    """Render playlist action buttons (Save, Export CSV, Download ZIP)"""
    col1, col2, col3 = st.columns(3)

    with col1:
        # Save playlist
        if st.button("💾 Save Playlist"):
            render_save_playlist_dialog()

    with col2:
        # Export CSV
        if st.button("📤 Export CSV"):
            render_export_csv()

    with col3:
        # Download all as ZIP
        if st.button("📦 Download All MP3s"):
            render_download_all_zip(tts_engine)


def render_save_playlist_dialog():
    """Render save playlist dialog"""
    with st.form("save_playlist_form"):
        playlist_name = st.text_input("Playlist Name", placeholder="My Playlist")

        submitted = st.form_submit_button("Save")

        if submitted:
            if not playlist_name:
                st.error("Please enter a playlist name")
            else:
                storage = StorageManager()
                if storage.save_playlist(playlist_name, st.session_state.tracks):
                    st.success(f"✅ Saved playlist '{playlist_name}'")
                else:
                    st.error("Failed to save playlist")


def render_export_csv():
    """Render CSV export"""
    storage = StorageManager()
    csv_content = storage.export_playlist_csv(st.session_state.tracks)

    st.download_button(
        label="Download CSV",
        data=csv_content,
        file_name=f"playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def render_download_all_zip(tts_engine):
    """Render download all tracks as ZIP"""
    if not st.session_state.get('api_key'):
        st.warning("Please enter your Google Cloud TTS API key first")
        return

    with st.spinner("Generating all audio files... This may take a while."):
        try:
            selected_voice = st.session_state.get('selected_voice', 'en-US-Standard-F')
            zip_bytes = create_playlist_zip(
                st.session_state.tracks,
                tts_engine,
                selected_voice
            )

            st.download_button(
                label="📥 Download ZIP",
                data=zip_bytes,
                file_name=f"playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )

            st.success("✅ ZIP file ready for download!")

        except Exception as e:
            st.error(f"Error generating ZIP: {str(e)}")
