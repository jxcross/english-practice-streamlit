import React, { useEffect, useRef, useState } from "react"
import { Streamlit, ComponentProps } from "streamlit-component-lib"
import WaveSurfer from "wavesurfer.js"
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.min.js"

interface WavesurferPlayerProps extends ComponentProps {
  audio_data: string
  repeat_mode: "none" | "one" | "all"
  playback_speed: number
  auto_play: boolean
}

const WavesurferPlayer: React.FC<WavesurferPlayerProps> = (props) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const wavesurferRef = useRef<WaveSurfer | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLooping, setIsLooping] = useState(false)
  const [selectedRegion, setSelectedRegion] = useState<any>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Create WaveSurfer instance
    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#90caf9",
      progressColor: "#1976d2",
      cursorColor: "#1976d2",
      height: 100,
      normalize: true,
      plugins: [RegionsPlugin.create()],
    })

    wavesurferRef.current = wavesurfer

    // Load audio
    wavesurfer.load(`data:audio/mp3;base64,${props.audio_data}`)

    // Event handlers
    wavesurfer.on("play", () => setIsPlaying(true))
    wavesurfer.on("pause", () => setIsPlaying(false))
    wavesurfer.on("ready", () => {
      setDuration(wavesurfer.getDuration())
      if (props.auto_play) {
        wavesurfer.play().catch(console.error)
      }
    })

    wavesurfer.on("timeupdate", (time) => {
      setCurrentTime(time)
    })

    // Handle finish event
    wavesurfer.on("finish", () => {
      console.log("Audio finished, repeat mode:", props.repeat_mode)

      // Region loop (highest priority)
      if (selectedRegion && selectedRegion.loop) {
        wavesurfer.setTime(selectedRegion.start)
        wavesurfer.play()
        return
      }

      // Global loop
      if (isLooping) {
        wavesurfer.play()
        return
      }

      // Repeat mode handling
      if (props.repeat_mode === "one") {
        // Repeat One: restart current track
        wavesurfer.seekTo(0)
        wavesurfer.play()
      } else {
        // Repeat All / None: notify Streamlit
        Streamlit.setComponentValue({
          event: "audio-ended",
          repeat_mode: props.repeat_mode,
          timestamp: Date.now(),
        })
      }
    })

    // Set playback speed
    if (props.playback_speed !== 1.0) {
      wavesurfer.setPlaybackRate(props.playback_speed)
    }

    // Cleanup
    return () => {
      wavesurfer.destroy()
    }
  }, [props.audio_data, props.repeat_mode, props.playback_speed, props.auto_play])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const handlePlayPause = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause()
    }
  }

  const handleStop = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.stop()
    }
  }

  const handleLoop = () => {
    setIsLooping(!isLooping)
  }

  const handleSpeedChange = (speed: number) => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(speed)
    }
  }

  return (
    <div style={{ padding: "10px", background: "#f0f2f6" }}>
      <div ref={containerRef} style={{ background: "white", borderRadius: "8px", padding: "10px", marginBottom: "10px" }} />
      
      <div style={{ display: "flex", gap: "8px", marginBottom: "10px", flexWrap: "wrap" }}>
        <button onClick={handlePlayPause} style={{ padding: "8px 16px", border: "none", borderRadius: "4px", background: "#1976d2", color: "white", cursor: "pointer" }}>
          {isPlaying ? "⏸ Pause" : "▶ Play"}
        </button>
        <button onClick={handleStop} style={{ padding: "8px 16px", border: "none", borderRadius: "4px", background: "#1976d2", color: "white", cursor: "pointer" }}>
          ⏹ Stop
        </button>
        <button onClick={handleLoop} style={{ padding: "8px 16px", border: "none", borderRadius: "4px", background: isLooping ? "#0d47a1" : "#1976d2", color: "white", cursor: "pointer" }}>
          {isLooping ? "🔁 Looping" : "🔁 Loop"}
        </button>
        <div style={{ display: "flex", gap: "4px", marginLeft: "auto" }}>
          {[0.5, 0.75, 1.0, 1.25, 1.5].map((speed) => (
            <button
              key={speed}
              onClick={() => handleSpeedChange(speed)}
              style={{
                padding: "6px 12px",
                border: "none",
                borderRadius: "4px",
                background: props.playback_speed === speed ? "#0d47a1" : "#1976d2",
                color: "white",
                cursor: "pointer",
                fontSize: "12px",
              }}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
      
      <div style={{ textAlign: "center", color: "#666", fontSize: "12px" }}>
        {formatTime(currentTime)} / {formatTime(duration)}
      </div>
    </div>
  )
}

export default WavesurferPlayer

