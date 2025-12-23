# WaveSurfer Player Custom Streamlit Component

This is a custom Streamlit component that provides a WaveSurfer.js audio player with full Python integration.

## Features

- Waveform visualization
- Play/Pause/Stop controls
- Loop functionality
- Playback speed control (0.5x to 1.5x)
- Region selection and looping
- Auto-play support
- Repeat mode support (none, one, all)
- **Full Python integration**: finish events are sent to Python via `Streamlit.setComponentValue()`

## Installation

1. Install dependencies:
```bash
cd components/wavesurfer_player/frontend
npm install
```

2. Build the component:
```bash
npm run build
```

3. The component will be automatically available in Python via:
```python
from components.wavesurfer_player import wavesurfer_player
```

## Usage

The component is automatically used when `use_custom_component=True` is passed to `render_audio_player()`.

Alternatively, you can use it directly:

```python
from components.wavesurfer_player import wavesurfer_player
import base64

# Encode audio to base64
audio_b64 = base64.b64encode(audio_bytes).decode()

# Use the component
result = wavesurfer_player(
    audio_data=audio_b64,
    repeat_mode="all",
    playback_speed=1.0,
    auto_play=True,
    key="player_1"
)

# Handle the result (audio-ended event)
if result and result.get('event') == 'audio-ended':
    # Handle next track
    pass
```

## Current Implementation

The current implementation uses `st.components.v1.html()` with `postMessage` and URL parameters for communication. This works but has limitations due to iframe sandbox restrictions.

The custom component provides a more reliable solution by using `Streamlit.setComponentValue()` directly.

