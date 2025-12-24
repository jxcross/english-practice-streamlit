import streamlit as st
import base64
from pathlib import Path
import json

st.title("자동 반복 오디오 + 스크립트 (스크롤 리스트) + Repeat One")

BASE = Path(__file__).parent
files = [BASE/"audio"/"a.mp3", BASE/"audio"/"b.mp3", BASE/"audio"/"c.mp3"]

scripts = [
  {
    "english": "Poverty is really linked to so many things in life.",
    "korean": "가난은 실제로 삶의 많은 부분과 연관되어 있습니다."
  },
  {
    "english": "Because it is not just an economic phenomenon.",
    "korean": "그것은 단순히 경제적인 현상이 아니기 때문입니다."
  },
  {
    "english": "It’s not just a social phenomenon.",
    "korean": "그것은 단순한 사회적 현상이 아닙니다."
  }
]

# 파일 확인
for f in files:
    if not f.exists():
        st.error(f"파일이 없습니다: {f}")
        st.stop()

# mp3 → base64
tracks = []
for f in files:
    tracks.append("data:audio/mpeg;base64," + base64.b64encode(f.read_bytes()).decode())

tracks_js = json.dumps(tracks)
scripts_js = json.dumps(scripts, ensure_ascii=False)

html = """
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

        <!-- ✅ Repeat One 토글 -->
        <label style="display:flex; align-items:center; gap:6px; user-select:none;">
          <input id="repeatOne" type="checkbox" />
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
               max-height:260px;   /* 2개 카드 높이 */
               overflow-y:auto;
               padding-right:4px;
             ">
        </div>
      </div>

    </div>

    <script>
      const tracks = __TRACKS__;
      const scripts = __SCRIPTS__;

      let index = 0;

      const audio = document.getElementById("player");
      const btn = document.getElementById("btn");
      const repeatOneEl = document.getElementById("repeatOne");

      const status = document.getElementById("status");
      const nowEn = document.getElementById("now_en");
      const nowKo = document.getElementById("now_ko");
      const listDiv = document.getElementById("list");

      function esc(s) {
        return String(s)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;");
      }

      function renderNow() {
        const s = scripts[index];
        const mode = repeatOneEl.checked ? "Repeat One" : "Repeat All";
        status.textContent = `Track ${index+1} / ${tracks.length}  ·  ${mode}`;
        nowEn.textContent = s.english;
        nowKo.textContent = s.korean;
      }

      function renderList() {
        let html = "";
        for (let i = 0; i < scripts.length; i++) {
          const s = scripts[i];
          const isCurrent = (i === index);
          html += `
            <div style="
              padding:10px;
              border:1px solid #eee;
              border-radius:8px;
              background:${isCurrent ? "#eef6ff" : "#fff"};
            ">
              <div style="font-family:monospace; margin-bottom:6px;">
                ${isCurrent ? "<b>=&gt;</b>" : "&nbsp;&nbsp;&nbsp;"} #${i+1}
              </div>
              <div>${esc(s.english)}</div>
              <div style="margin-top:4px; opacity:0.85;">${esc(s.korean)}</div>
            </div>
          `;
        }
        listDiv.innerHTML = html;
      }

      function loadTrack(i) {
        index = i;
        audio.src = tracks[index];
        renderNow();
        renderList();
      }

      function playCurrent() {
        const p = audio.play();
        if (p) p.catch(() => {});
      }

      // 초기 로드
      loadTrack(0);

      btn.onclick = () => playCurrent();

      // Repeat One 토글 바뀌면 상태표시 갱신
      repeatOneEl.addEventListener("change", () => {
        renderNow();
      });

      // 곡 끝났을 때 동작
      audio.addEventListener("ended", () => {
        if (repeatOneEl.checked) {
          // ✅ 한 곡 반복
          loadTrack(index);
          playCurrent();
        } else {
          // ✅ 전체 반복(다음 곡)
          loadTrack((index + 1) % tracks.length);
          playCurrent();
        }
      });

      audio.addEventListener("play", () => {
        renderNow();
        renderList();
      });
    </script>
  </body>
</html>
""".replace("__TRACKS__", tracks_js).replace("__SCRIPTS__", scripts_js)

st.components.v1.html(html, height=600)
