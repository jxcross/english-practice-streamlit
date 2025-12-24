"""
Audio player module for playback and MP3 download functionality
"""
import streamlit as st
import base64
from utils.audio_utils import format_time, generate_filename, get_audio_duration_from_bytes


def render_audio_player(audio_bytes_list, tracks, current_track_idx, show_download=True, use_custom_component=False):
    """
    Render audio player with JS-based track switching using st.components.v1.html

    Args:
        audio_bytes_list: List of MP3 audio bytes for all tracks
        tracks: List of track dictionaries [{'english': '...', 'korean': '...'}, ...]
        current_track_idx: Current track index (0-based)
        show_download: Whether to show download button
        use_custom_component: Ignored (kept for compatibility)

    Returns:
        None
    """
    if not audio_bytes_list or not tracks:
        st.warning("No audio generated")
        return

    # Get current state
    repeat_mode = st.session_state.get('repeat_mode', 'none')
    
    # Get current track info for display
    current_track = tracks[current_track_idx] if current_track_idx < len(tracks) else tracks[0]
    current_audio = audio_bytes_list[current_track_idx] if current_track_idx < len(audio_bytes_list) else audio_bytes_list[0]
    
    # Get audio duration for current track
    try:
        duration = get_audio_duration_from_bytes(current_audio)
        st.caption(f"Duration: {format_time(duration)}")
    except Exception:
        pass

    # Convert all audio bytes to base64 data URLs
    import json
    tracks_data_urls = []
    for audio_bytes in audio_bytes_list:
        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode()
            tracks_data_urls.append(f"data:audio/mpeg;base64,{b64}")
        else:
            tracks_data_urls.append(None)
    
    # Ensure current_track_idx is valid
    if current_track_idx >= len(tracks_data_urls):
        current_track_idx = 0
    
    # Prepare tracks and scripts data for JS
    tracks_js = json.dumps(tracks_data_urls)
    scripts_js = json.dumps(tracks, ensure_ascii=False)
    
    # Determine initial repeat one state
    initial_repeat_one = (repeat_mode == 'one')
    
    # Create HTML component with enhanced JS player
    html = f"""
<!doctype html>
<html>
  <body style="margin:0; padding:12px; font-family:sans-serif;">
    <div style="padding:10px; border:1px solid #ddd; border-radius:10px;">

      <!-- 상단: 현재 스크립트 -->
      <div style="margin-bottom:12px;">
        <div id="status" style="font-size:13px; opacity:0.75;"></div>
        <div style="margin-top:6px; padding:10px; background:#f7f7f7; border-radius:8px;">
          <div style="font-weight:700; font-size:14px; margin-bottom:6px;">Now Playing</div>
          <div id="now_en" style="font-size:18px; line-height:1.5;"></div>
          <div id="now_ko" style="margin-top:6px; font-size:18px; line-height:1.6;"></div>
        </div>
      </div>

      <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
        <button id="btn">Play (click once)</button>

        <!-- Repeat One 토글 -->
        <label style="display:flex; align-items:center; gap:6px; user-select:none;">
          <input id="repeatOne" type="checkbox" {'checked' if initial_repeat_one else ''} />
          Repeat One (한곡 반복)
        </label>
      </div>

      <audio id="player" controls style="width:100%; margin-top:8px;"></audio>

      <!-- 하단: 스크립트 리스트 (2개 높이 + 스크롤) -->
      <div style="margin-top:16px;">
        <div style="font-weight:700; font-size:14px; margin-bottom:6px;">
          Script List (scroll)
        </div>

        <div id="list"
             style="
               display:flex;
               flex-direction:column;
               gap:10px;
               max-height:260px;
               overflow-y:auto;
               padding-right:4px;
             ">
        </div>
      </div>

    </div>

<script>
      const tracks = {tracks_js};
      const scripts = {scripts_js};

      let index = {current_track_idx};

      const audio = document.getElementById("player");
      const btn = document.getElementById("btn");
      const repeatOneEl = document.getElementById("repeatOne");

      const status = document.getElementById("status");
      const nowEn = document.getElementById("now_en");
      const nowKo = document.getElementById("now_ko");
      const listDiv = document.getElementById("list");

      function esc(s) {{
        return String(s)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;");
      }}

      function renderNow() {{
        const s = scripts[index];
        const mode = repeatOneEl.checked ? "Repeat One" : "Repeat All";
        status.textContent = `Track ${{index+1}} / ${{tracks.length}}  ·  ${{mode}}`;
        nowEn.textContent = s.english;
        nowKo.textContent = s.korean;
      }}

      function renderList() {{
        let html = "";
        for (let i = 0; i < scripts.length; i++) {{
          const s = scripts[i];
          const isCurrent = (i === index);
          html += `
            <div style="
              padding:10px;
              border:1px solid #eee;
              border-radius:8px;
              background:${{isCurrent ? "#eef6ff" : "#fff"}};
            ">
              <div style="font-family:monospace; margin-bottom:6px;">
                ${{isCurrent ? "<b>=&gt;</b>" : "&nbsp;&nbsp;&nbsp;"}} #${{i+1}}
              </div>
              <div>${{esc(s.english)}}</div>
              <div style="margin-top:4px; opacity:0.85;">${{esc(s.korean)}}</div>
            </div>
          `;
        }}
        listDiv.innerHTML = html;
      }}

      function loadTrack(i) {{
        if (i < 0 || i >= tracks.length || !tracks[i]) return;
        index = i;
        audio.src = tracks[index];
        renderNow();
        renderList();
      }}

      function playCurrent() {{
        const p = audio.play();
        if (p) p.catch(() => {{}});
      }}

      // 초기 로드
      loadTrack({current_track_idx});

      btn.onclick = () => playCurrent();

      // Repeat One 토글 바뀌면 상태표시 갱신
      repeatOneEl.addEventListener("change", () => {{
        renderNow();
      }});

      // 곡 끝났을 때 동작
      audio.addEventListener("ended", () => {{
        if (repeatOneEl.checked) {{
          // ✅ 한 곡 반복
          loadTrack(index);
          playCurrent();
        }} else {{
          // ✅ 전체 반복(다음 곡) - 마지막에서도 첫 번째로 돌아감
          loadTrack((index + 1) % tracks.length);
          playCurrent();
        }}
      }});
                
      audio.addEventListener("play", () => {{
        renderNow();
        renderList();
      }});
</script>
  </body>
</html>
"""
    
    # Render using st.components.v1.html
    st.components.v1.html(html, height=600)

    # Download button for current track
    if show_download:
        render_download_button(current_track, current_audio, current_track_idx)




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
