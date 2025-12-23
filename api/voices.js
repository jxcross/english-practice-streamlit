// Get available voices from Google Cloud TTS API
module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS request (preflight)
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow GET requests
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const apiKey = req.query.apiKey;
    const languageCode = req.query.languageCode || 'en-US'; // Default to English

    // Validation
    if (!apiKey) {
      res.status(400).json({ error: 'API key is required' });
      return;
    }

    // Call Google Cloud TTS API to get voices
    const url = `https://texttospeech.googleapis.com/v1/voices?languageCode=${languageCode}&key=${apiKey}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Google TTS Voices API Error:', errorData);

      if (response.status === 403 || response.status === 401) {
        res.status(401).json({ error: 'Authentication failed', details: 'Check API key' });
      } else {
        res.status(response.status).json({
          error: 'Voices API error',
          details: errorData.error?.message || 'Unknown error'
        });
      }
      return;
    }

    const data = await response.json();

    // Set cache headers (24 hours - voices don't change often)
    res.setHeader('Cache-Control', 'public, max-age=86400');

    // Return formatted voices list
    res.status(200).json({
      voices: data.voices || [],
      languageCode
    });

  } catch (error) {
    console.error('Voices API Error:', error);
    res.status(500).json({
      error: 'Internal server error',
      details: error.message
    });
  }
};

