# Assets Directory

This directory contains all logo and icon files for the English Practice Player application.

## Logo Files

### Source
- **logo.png** (1024x1024, 699KB) - Original high-resolution logo

### App Icons (Multiple Sizes)
- **logo-512.png** (512x512, 199KB) - High resolution
- **logo-256.png** (256x256, 53KB) - Header display in upload screen
- **logo-128.png** (128x128, 16KB) - Page favicon, player screen header
- **logo-64.png** (64x64, 4.8KB) - Small icon
- **logo-32.png** (32x32, 1.5KB) - Favicon size
- **logo-16.png** (16x16, 595B) - Minimum favicon

## Usage in App

### Page Icon (Favicon)
- **File**: `logo-128.png`
- **Location**: `app.py:15` - `st.set_page_config(page_icon="assets/logo-128.png")`
- **Display**: Browser tab favicon

### Upload Screen Header
- **File**: `logo-256.png`
- **Location**: `app.py:85` - Upload screen header (120px width)
- **Display**: Main logo next to title

### Player Screen Header
- **File**: `logo-128.png`
- **Location**: `app.py:132` - Player screen header (60px width)
- **Display**: Compact logo in player view

## Design Specifications

### Style
- **Theme**: Professional/Business
- **Design**: Modern, minimal, geometric
- **Purpose**: English learning audio player application

### Color Palette
- **Background**: Deep Navy Blue `#0a0e27`
- **Primary**: Corporate Blue `#2196F3` to `#1976D2` (gradient)
- **Accent**: White `#FFFFFF` and Light Blue `#64B5F6`

### Concept
Professional app icon representing:
- **Global English Learning**: Globe element
- **Audio Technology**: Sound waveforms
- **TTS Functionality**: Audio/speech elements

## File History

- **Original Icon**: `icon.svg` (backed up to `icon.svg.backup`)
  - Previous emoji-based icon: 🎵
  - Replaced with professional logo design

## Regeneration

If you need to regenerate sizes from the source logo:

```bash
# Using macOS sips
sips -z 512 512 logo.png --out logo-512.png
sips -z 256 256 logo.png --out logo-256.png
sips -z 128 128 logo.png --out logo-128.png
sips -z 64 64 logo.png --out logo-64.png
sips -z 32 32 logo.png --out logo-32.png
sips -z 16 16 logo.png --out logo-16.png
```

## Notes

- All PNG files optimized for web use
- Transparent backgrounds recommended for future versions
- SVG version can be created for scalability if needed
