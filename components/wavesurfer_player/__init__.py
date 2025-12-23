"""
Custom Streamlit Component for WaveSurfer.js Audio Player
"""
import streamlit.components.v1 as components

# Create the component
_wavesurfer_component = components.declare_component(
    "wavesurfer_player",
    path="./components/wavesurfer_player"
)

def wavesurfer_player(
    audio_data,
    repeat_mode="none",
    playback_speed=1.0,
    auto_play=False,
    key=None
):
    """
    Custom Streamlit component for WaveSurfer.js audio player
    
    Args:
        audio_data: Base64 encoded audio data
        repeat_mode: Repeat mode ('none', 'one', 'all')
        playback_speed: Playback speed (0.5 to 2.0)
        auto_play: Whether to auto-play on load
        key: Component key
    
    Returns:
        dict: Event data when audio ends, None otherwise
    """
    return _wavesurfer_component(
        audio_data=audio_data,
        repeat_mode=repeat_mode,
        playback_speed=playback_speed,
        auto_play=auto_play,
        key=key
    )

