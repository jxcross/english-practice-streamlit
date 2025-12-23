// Use native fetch to call Google Cloud TTS REST API directly
module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS request (preflight)
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow POST requests
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const { text, voice = 'en-US-Standard-F', languageCode, model, speed = 1.0, apiKey } = req.body;

    // Validation
    if (!apiKey) {
      res.status(400).json({ error: 'API key is required' });
      return;
    }

    if (!text) {
      res.status(400).json({ error: 'Text is required' });
      return;
    }

    if (text.length > 5000) {
      res.status(400).json({ error: 'Text too long (max 5000 characters)' });
      return;
    }

    if (speed < 0.25 || speed > 4.0) {
      res.status(400).json({ error: 'Speed must be between 0.25 and 4.0' });
      return;
    }

    // Determine language code
    let finalLanguageCode = languageCode;
    if (!finalLanguageCode) {
      // Try to extract from voice name (fallback for backward compatibility)
      // Format: "en-US-Neural2-D" -> "en-US"
      const match = voice.match(/^([a-z]{2}-[A-Z]{2})-/);
      if (match) {
        finalLanguageCode = match[1];
      } else {
        // Default fallback
        finalLanguageCode = 'en-US';
      }
    }

    // Build SSML without speed control (speed is handled by client playbackRate)
    const ssml = `<speak>${escapeXml(text)}</speak>`;

    // Build voice object
    const voiceObj = {
      languageCode: finalLanguageCode,
      name: voice
    };

    // Add model if provided (required for some voices like Gemini)
    if (model) {
      voiceObj.model = model;
    }

    // Build request body for Google Cloud TTS REST API
    const requestBody = {
      input: { ssml },
      voice: voiceObj,
      audioConfig: {
        audioEncoding: 'MP3',
        speakingRate: 1.0,
        pitch: 0.0,
        volumeGainDb: 0.0
      }
    };

    // Call Google Cloud TTS REST API
    const response = await fetch(
      `https://texttospeech.googleapis.com/v1/text:synthesize?key=${apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Google TTS API Error:', errorData);

      if (response.status === 429) {
        res.status(429).json({ error: 'Quota exceeded', details: 'Monthly limit reached' });
      } else if (response.status === 403 || response.status === 401) {
        res.status(401).json({ error: 'Authentication failed', details: 'Check API key' });
      } else {
        res.status(response.status).json({
          error: 'TTS API error',
          details: errorData.error?.message || 'Unknown error'
        });
      }
      return;
    }

    const data = await response.json();

    // Get base64 audio from response
    const audioBase64 = data.audioContent;

    // Estimate duration (rough, will be corrected by HTML5 Audio API)
    // Duration is calculated at 1.0x speed, actual playback speed is handled by client playbackRate
    const estimatedDuration = text.length * 150;

    // Set cache headers (30 days)
    res.setHeader('Cache-Control', 'public, max-age=2592000');

    // Return response
    res.status(200).json({
      audio: audioBase64,
      estimatedDuration,
      voice,
      speed,
      characters: text.length
    });

  } catch (error) {
    console.error('TTS Error:', error);
    res.status(500).json({
      error: 'Internal server error',
      details: error.message
    });
  }
};

// Helper function to escape XML/HTML special characters for SSML
function escapeXml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
