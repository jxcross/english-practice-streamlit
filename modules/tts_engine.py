"""
TTS Engine with Google Cloud Text-to-Speech integration and caching
Uses REST API with API key for authentication
"""
import hashlib
import requests
import base64
from utils.cache_manager import CacheManager
from utils.audio_utils import estimate_duration


class TTSEngine:
    """Google Cloud TTS engine with caching support (REST API)"""

    def __init__(self, api_key=None, cache_dir='data/cache'):
        self.api_key = api_key
        self.cache = CacheManager(cache_dir=cache_dir, max_size_mb=100, ttl_days=30)
        self.base_url = "https://texttospeech.googleapis.com/v1"

    def generate_audio(self, text, voice='en-US-Standard-F', language_code='en-US'):
        """
        Generate audio from text using Google Cloud TTS REST API

        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., 'en-US-Standard-F')
            language_code: Language code (e.g., 'en-US')

        Returns:
            tuple: (audio_bytes, duration, cache_hit)
        """
        # Generate cache key
        cache_key = self._generate_cache_key(text, voice)

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached['audio'], cached['duration'], True

        # Check API key
        if not self.api_key:
            raise Exception("TTS client not initialized. Please provide a valid API key.")

        try:
            # Extract language code from voice name if not provided
            if '-' in voice:
                voice_parts = voice.split('-')
                language_code = f"{voice_parts[0]}-{voice_parts[1]}"

            # Prepare request
            url = f"{self.base_url}/text:synthesize?key={self.api_key}"

            headers = {
                'Content-Type': 'application/json'
            }

            data = {
                'input': {
                    'text': text
                },
                'voice': {
                    'languageCode': language_code,
                    'name': voice
                },
                'audioConfig': {
                    'audioEncoding': 'MP3',
                    'speakingRate': 1.0,
                    'pitch': 0.0,
                    'volumeGainDb': 0.0
                }
            }

            # Make request
            response = requests.post(url, json=data, headers=headers)

            # Check response
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                raise Exception(f"API request failed: {error_msg}")

            # Extract audio content
            result = response.json()
            audio_content_base64 = result.get('audioContent')

            if not audio_content_base64:
                raise Exception("No audio content in response")

            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_content_base64)
            duration = estimate_duration(text)

            # Cache for future use
            self.cache.set(cache_key, {
                'audio': audio_bytes,
                'duration': duration,
                'text_preview': text[:100],
                'voice': voice
            })

            return audio_bytes, duration, False

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")

    def get_available_voices(self, language_code='en'):
        """
        Fetch available voices from Google Cloud TTS REST API

        Args:
            language_code: Language code filter (e.g., 'en')

        Returns:
            list: List of voice dictionaries
        """
        if not self.api_key:
            return []

        try:
            # Make request to list voices
            url = f"{self.base_url}/voices?key={self.api_key}"

            if language_code:
                url += f"&languageCode={language_code}"

            response = requests.get(url)

            if response.status_code != 200:
                print(f"Error fetching voices: {response.status_code}")
                return []

            result = response.json()
            all_voices = result.get('voices', [])

            voices = []
            for voice in all_voices:
                voice_name = voice.get('name', '')

                # Filter for Standard, WaveNet, and Neural2 voices (en-US, en-GB, en-AU)
                if any(voice_name.startswith(prefix) for prefix in [
                    'en-US-Standard-', 'en-GB-Standard-', 'en-AU-Standard-',
                    'en-US-Wavenet-', 'en-GB-Wavenet-', 'en-AU-Wavenet-',
                    'en-US-Neural2-', 'en-GB-Neural2-', 'en-AU-Neural2-'
                ]):
                    language_codes = voice.get('languageCodes', [])
                    ssml_gender = voice.get('ssmlGender', 'NEUTRAL')

                    voices.append({
                        'name': voice_name,
                        'language_code': language_codes[0] if language_codes else 'en-US',
                        'ssml_gender': self._format_gender(ssml_gender),
                        'description': self._format_voice_description(voice)
                    })

            return sorted(voices, key=lambda x: x['name'])

        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []

    def _generate_cache_key(self, text, voice):
        """
        Generate cache key from text and voice (same as PWA)

        Args:
            text: Text string
            voice: Voice name

        Returns:
            str: SHA256 hash of text + voice
        """
        combined = f"{text}_{voice}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _format_gender(self, ssml_gender):
        """Format SSML gender string"""
        gender_map = {
            'MALE': 'Male',
            'FEMALE': 'Female',
            'NEUTRAL': 'Neutral',
            'SSML_VOICE_GENDER_UNSPECIFIED': 'Unknown'
        }
        return gender_map.get(ssml_gender, 'Unknown')

    def _format_voice_description(self, voice):
        """
        Format voice description

        Args:
            voice: Voice object from Google Cloud TTS API

        Returns:
            str: Formatted description (e.g., "US Female Standard (F)")
        """
        voice_name = voice.get('name', '')

        # Extract language label
        if 'en-US' in voice_name:
            lang_label = 'US'
        elif 'en-GB' in voice_name:
            lang_label = 'UK'
        elif 'en-AU' in voice_name:
            lang_label = 'AU'
        else:
            lang_label = 'EN'

        # Extract gender
        ssml_gender = voice.get('ssmlGender', 'NEUTRAL')
        gender_label = self._format_gender(ssml_gender)

        # Extract voice type and ID
        if 'Neural2' in voice_name:
            voice_type = 'Neural2'
        elif 'Wavenet' in voice_name:
            voice_type = 'WaveNet'
        elif 'Standard' in voice_name:
            voice_type = 'Standard'
        else:
            voice_type = 'Standard'

        # Extract voice ID (last character)
        voice_id = voice_name.split('-')[-1]

        return f"{lang_label} {gender_label} {voice_type} ({voice_id})"

    def get_cache_stats(self):
        """Get cache statistics"""
        return self.cache.get_stats()
