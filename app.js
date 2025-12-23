// State management
let tracks = [];
let currentTrack = 0;
let isPlaying = false;
let isPaused = false;
let playbackSpeed = 1.0;
let repeatMode = 'none'; // 'none', 'one', 'all'
let utterance = null;
let progressInterval = null;
let currentProgress = 0; // Track actual progress from onboundary
let selectedVoice = null; // Selected voice for TTS
let pausedCharIndex = 0; // Track pause position for Web Speech API

// Google TTS state
let audioElement = null;  // HTML5 Audio element
let audioCache = null;    // IndexedDB database
let isLoadingAudio = false;
let cachedBlobURLs = new Map();  // Track blob URLs for cleanup
let currentTTSMode = 'auto';  // 'auto', 'google', 'webspeech'

// API Key management (memory only - security first)
let googleCloudTtsApiKey = null;  // Stored in memory only, never in localStorage

// iOS Speech Synthesis fix
let speechSynthesisInitialized = false;
let speechSynthesisReady = false;

// ====================================================================
// DEBUG LOGGING (for mobile debugging)
// ====================================================================
let debugLogs = [];
const MAX_DEBUG_LOGS = 50;
let isLogging = false; // 무한 재귀 방지 플래그

// 원본 console 메서드 저장 (addDebugLog에서 사용)
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleLog = console.log;

function addDebugLog(message, type = 'log') {
    // 무한 재귀 방지
    if (isLogging) return;
    
    isLogging = true;
    
    try {
        const timestamp = new Date().toLocaleTimeString();
        debugLogs.unshift({ timestamp, message, type });
        if (debugLogs.length > MAX_DEBUG_LOGS) {
            debugLogs.pop();
        }
        
        // 원본 console 메서드 사용 (래핑된 것을 호출하지 않음)
        if (type === 'error') {
            originalConsoleError(`[${timestamp}] ${message}`);
        } else if (type === 'warn') {
            originalConsoleWarn(`[${timestamp}] ${message}`);
        } else {
            originalConsoleLog(`[${timestamp}] ${message}`);
        }
        
        // 화면에 표시
        updateDebugPanel();
    } finally {
        isLogging = false;
    }
}

function updateDebugPanel() {
    const panel = document.getElementById('debugPanel');
    if (!panel) return;
    
    try {
        const logHTML = debugLogs.map(log => {
            const color = log.type === 'error' ? '#ff4444' : 
                         log.type === 'warn' ? '#ffaa00' : '#00ff00';
            return `<div style="color: ${color}; font-size: 11px; margin: 2px 0; word-break: break-word;">
                [${log.timestamp}] ${log.message}
            </div>`;
        }).join('');
        
        panel.innerHTML = logHTML;
        panel.scrollTop = 0; // 최신 로그가 위에 표시되므로 스크롤을 맨 위로
    } catch (e) {
        // updateDebugPanel에서 오류가 발생해도 무한 재귀를 방지
        originalConsoleError('Error updating debug panel:', e);
    }
}

// 디버그 패널 토글 함수
function toggleDebugPanel() {
    const panel = document.getElementById('debugPanel');
    const button = document.getElementById('debugToggleBtn');
    if (panel) {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        if (button) {
            button.textContent = isVisible ? '🐛 Debug' : '❌ Close';
        }
    }
}

// 전역 스코프에 명시적으로 노출 (HTML onclick 속성에서 사용)
window.toggleDebugPanel = toggleDebugPanel;

// 기존 console 메서드를 래핑하여 디버그 로그에도 기록
(function() {
    console.error = function(...args) {
        if (!isLogging) {
            addDebugLog(args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' '), 'error');
        }
        originalConsoleError.apply(console, args);
    };

    console.warn = function(...args) {
        if (!isLogging) {
            addDebugLog(args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' '), 'warn');
        }
        originalConsoleWarn.apply(console, args);
    };

    console.log = function(...args) {
        if (!isLogging) {
            addDebugLog(args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' '), 'log');
        }
        originalConsoleLog.apply(console, args);
    };
})();

// Sample data
const sampleTracks = [
    {
        english: "So, today was our VSMR quarterly wrap-up meeting.",
        korean: "오늘은 VSMR 분기 총괄회의가 있었어요."
    },
    {
        english: "We reviewed all the major projects from Q4.",
        korean: "우리는 4분기의 모든 주요 프로젝트를 검토했습니다."
    },
    {
        english: "The presentation was really well organized.",
        korean: "발표는 정말 잘 구성되어 있었어요."
    },
    {
        english: "I think we exceeded our targets this quarter.",
        korean: "이번 분기에 목표를 초과 달성한 것 같아요."
    },
    {
        english: "The team collaboration has been outstanding.",
        korean: "팀 협업이 정말 훌륭했습니다."
    },
    {
        english: "We need to improve our communication channels.",
        korean: "우리는 커뮤니케이션 채널을 개선해야 합니다."
    },
    {
        english: "The client feedback was overwhelmingly positive.",
        korean: "고객 피드백은 압도적으로 긍정적이었습니다."
    },
    {
        english: "Let's celebrate our achievements together.",
        korean: "함께 우리의 성과를 축하합시다."
    },
    {
        english: "Next quarter looks very promising.",
        korean: "다음 분기는 매우 유망해 보입니다."
    },
    {
        english: "I'm excited about the new initiatives.",
        korean: "새로운 계획들이 기대됩니다."
    },
    {
        english: "We should schedule a follow-up meeting soon.",
        korean: "곧 후속 회의를 예약해야 합니다."
    },
    {
        english: "The data analysis revealed interesting insights.",
        korean: "데이터 분석에서 흥미로운 통찰이 드러났습니다."
    },
    {
        english: "Everyone contributed their best work.",
        korean: "모두가 최선을 다해 기여했습니다."
    },
    {
        english: "The budget allocation seems reasonable.",
        korean: "예산 배분이 합리적으로 보입니다."
    },
    {
        english: "We're building momentum for next year.",
        korean: "내년을 위한 탄력을 만들고 있습니다."
    },
    {
        english: "Thank you all for your hard work.",
        korean: "모두 수고하셨습니다."
    }
];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // 첫 클릭 시 iOS 초기화 (이 부분 추가)
    document.body.addEventListener('click', () => {
        if (isIOS() && !speechSynthesisInitialized) {
            initSpeechSynthesisForIOS();
        }
    }, { once: true });

    // iOS Chrome: Clear saved voice if it's not in the safe list
    if (isIOSChrome()) {
        const savedVoice = localStorage.getItem('selectedBrowserVoice');
        if (savedVoice) {
            const safeVoiceNames = ['Samantha', 'Aaron', 'Nicky', 'Fred', 'Victoria', 'Karen'];
            if (!safeVoiceNames.includes(savedVoice)) {
                console.log(`[iOS Chrome] Removing unsafe saved voice: ${savedVoice}`);
                localStorage.removeItem('selectedBrowserVoice');
                selectedVoice = null;
            }
        }
    }

    loadSavedPlaylists();
    setupEventListeners();
    // Don't load voices here - let loadTTSMode() handle it based on selected mode

    // Initialize Google TTS
    try {
        await initAudioCache();
        clearApiKeyOnUnload(); // Register beforeunload handler
        updateApiKeyStatus(); // Update API key status display (this also calls updateApiKeyStatusUpload and updateTTSModeOptions)
        loadTTSMode(); // This will load voices if Google mode is selected
        console.log('Google TTS initialized');
    } catch (error) {
        console.error('Failed to initialize Google TTS:', error);
    }
    
    // Debug panel auto-show if ?debug=1 in URL
    if (new URLSearchParams(window.location.search).get('debug') === '1') {
        const panel = document.getElementById('debugPanel');
        const button = document.getElementById('debugToggleBtn');
        if (panel) panel.style.display = 'block';
        if (button) button.textContent = '❌ Close';
    }
});

function setupEventListeners() {
    // CSV Upload
    document.getElementById('csvUpload').addEventListener('change', handleCSVUpload);
    
    // API Key Input in Upload Card - Enter key support
    const apiKeyInputUpload = document.getElementById('apiKeyInputUpload');
    if (apiKeyInputUpload) {
        apiKeyInputUpload.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                saveApiKeyFromUpload();
            }
        });
    }
}

// ====================================================================
// API KEY MANAGEMENT (Memory Only - Security First)
// ====================================================================

// Get API key from memory
function getApiKey() {
    return googleCloudTtsApiKey;
}

// Save API key to memory (never to localStorage)
function saveApiKey(apiKey) {
    if (!validateApiKey(apiKey)) {
        return false;
    }
    googleCloudTtsApiKey = apiKey.trim();
    updateApiKeyStatus();
    return true;
}

// Delete API key from memory
function deleteApiKey() {
    googleCloudTtsApiKey = null;
    updateApiKeyStatus();
    showNotification('✅ API key deleted from memory', 'success');
}

// Check if API key exists
function hasApiKey() {
    return googleCloudTtsApiKey !== null && googleCloudTtsApiKey.length > 0;
}

// Mask API key for display (first 6 chars + ...****)
function maskApiKey(apiKey) {
    if (!apiKey || apiKey.length < 6) return '****';
    return apiKey.substring(0, 6) + '...****';
}

// Validate API key format
function validateApiKey(apiKey) {
    if (!apiKey || typeof apiKey !== 'string') {
        return false;
    }
    const trimmed = apiKey.trim();
    if (trimmed.length < 39) {
        return false;
    }
    // Google API keys typically start with "AIzaSy"
    if (!trimmed.startsWith('AIzaSy')) {
        return false;
    }
    return true;
}

// Update API key status display
function updateApiKeyStatus() {
    // Update upload card status
    updateApiKeyStatusUpload();
    // Update TTS mode options based on API key
    updateTTSModeOptions();
}

// Update API key status display in upload card
function updateApiKeyStatusUpload() {
    const statusValueEl = document.getElementById('apiKeyStatusValueUpload');
    const deleteBtn = document.getElementById('apiKeyDeleteBtnUpload');
    
    if (!statusValueEl) return;
    
    if (hasApiKey()) {
        statusValueEl.textContent = maskApiKey(googleCloudTtsApiKey);
        statusValueEl.classList.add('set');
        if (deleteBtn) deleteBtn.style.display = 'block';
    } else {
        statusValueEl.textContent = 'Not Set';
        statusValueEl.classList.remove('set');
        if (deleteBtn) deleteBtn.style.display = 'none';
    }
}

// Save API key from upload card
function saveApiKeyFromUpload() {
    const input = document.getElementById('apiKeyInputUpload');
    const error = document.getElementById('apiKeyErrorUpload');
    
    if (!input) return;
    
    const apiKey = input.value.trim();
    
    // Validate
    if (!apiKey) {
        showNotification('❌ API key를 입력해주세요.', 'error');
        return;
    }
    
    if (!validateApiKey(apiKey)) {
        showNotification('❌ 잘못된 API key 형식입니다. Google API key는 "AIzaSy"로 시작하고 최소 39자 이상이어야 합니다.', 'error');
        return;
    }
    
    // Save
    if (saveApiKey(apiKey)) {
        input.value = '';
        showNotification('✅ API key가 저장되었습니다 (메모리만 저장)', 'success');
        // Load voices if Google mode is selected
        if (currentTTSMode === 'google') {
            loadVoices().catch(error => {
                console.error('Error loading voices:', error);
            });
        }
    } else {
        showNotification('❌ API key 저장에 실패했습니다.', 'error');
    }
}

// Delete API key from upload card
function deleteApiKeyFromUpload() {
    deleteApiKey();
    const input = document.getElementById('apiKeyInputUpload');
    if (input) input.value = '';
}

// Toggle API key visibility in upload card
function toggleApiKeyVisibilityUpload() {
    const input = document.getElementById('apiKeyInputUpload');
    const toggleBtn = document.getElementById('toggleVisibilityBtnUpload');
    
    if (!input || !toggleBtn) return;
    
    if (input.type === 'password') {
        input.type = 'text';
        toggleBtn.textContent = '🙈';
    } else {
        input.type = 'password';
        toggleBtn.textContent = '👁️';
    }
}

// Update TTS mode options based on API key availability
function updateTTSModeOptions() {
    const select = document.getElementById('ttsModeSelect');
    if (!select) return;
    
    const hasKey = hasApiKey();
    const googleOption = select.querySelector('option[value="google"]');
    
    if (googleOption) {
        if (hasKey) {
            googleOption.disabled = false;
            googleOption.textContent = 'Google Cloud (High Quality)';
        } else {
            googleOption.disabled = true;
            googleOption.textContent = 'Google Cloud (API Key Required)';
            // If Google mode is selected but no API key, switch to auto
            if (select.value === 'google') {
                select.value = 'auto';
                currentTTSMode = 'auto';
                localStorage.setItem('ttsMode', 'auto');
            }
        }
    }
}

// Show API key input modal
function showApiKeyModal() {
    const modal = document.getElementById('apiKeyModal');
    const input = document.getElementById('apiKeyInput');
    const error = document.getElementById('apiKeyError');
    
    if (!modal || !input) return;
    
    // Clear previous input and error
    input.value = '';
    error.style.display = 'none';
    error.textContent = '';
    
    // Show modal
    modal.style.display = 'flex';
    
    // Focus input and add Enter key handler
    setTimeout(() => {
        input.focus();
        input.onkeydown = (e) => {
            if (e.key === 'Enter') {
                saveApiKeyFromModal();
            } else if (e.key === 'Escape') {
                closeApiKeyModal();
            }
        };
    }, 100);
}

// Close API key modal
function closeApiKeyModal() {
    const modal = document.getElementById('apiKeyModal');
    const input = document.getElementById('apiKeyInput');
    const error = document.getElementById('apiKeyError');
    
    if (modal) modal.style.display = 'none';
    if (input) input.value = '';
    if (error) {
        error.style.display = 'none';
        error.textContent = '';
    }
}

// Save API key from modal
function saveApiKeyFromModal() {
    const input = document.getElementById('apiKeyInput');
    const error = document.getElementById('apiKeyError');
    
    if (!input || !error) return;
    
    const apiKey = input.value.trim();
    
    // Validate
    if (!apiKey) {
        error.textContent = 'API key cannot be empty';
        error.style.display = 'block';
        return;
    }
    
    if (!validateApiKey(apiKey)) {
        error.textContent = 'Invalid API key format. Google API keys should start with "AIzaSy" and be at least 39 characters long.';
        error.style.display = 'block';
        return;
    }
    
    // Save
    if (saveApiKey(apiKey)) {
        closeApiKeyModal();
        showNotification('✅ API key saved (memory only)', 'success');
    } else {
        error.textContent = 'Failed to save API key';
        error.style.display = 'block';
    }
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
    const input = document.getElementById('apiKeyInput');
    const toggleBtn = document.getElementById('toggleVisibilityBtn');
    
    if (!input || !toggleBtn) return;
    
    if (input.type === 'password') {
        input.type = 'text';
        toggleBtn.textContent = '🙈';
    } else {
        input.type = 'password';
        toggleBtn.textContent = '👁️';
    }
}

// Clear API key on page unload (security)
function clearApiKeyOnUnload() {
    window.addEventListener('beforeunload', () => {
        googleCloudTtsApiKey = null;
    });
}

// Store loaded voices from API
let googleVoicesList = [];

// Load available voices from Google Cloud TTS API
async function loadVoices() {
    const voiceSelect = document.getElementById('voiceSelect');
    
    if (!voiceSelect) return;

    // Check if API key is available
    if (!hasApiKey()) {
        voiceSelect.innerHTML = '';
        const autoOption = document.createElement('option');
        autoOption.value = '';
        autoOption.textContent = 'Auto (Best English)';
        voiceSelect.appendChild(autoOption);
        voiceSelect.disabled = true;
        showNotification('⚠️ API key가 필요합니다. 업로드 화면에서 API key를 입력해주세요.', 'warning');
        return;
    }

    // Show loading state
    voiceSelect.disabled = true;
    
    // Clear all options first
    voiceSelect.innerHTML = '';
    
    // Add loading option
    const loadingOption = document.createElement('option');
    loadingOption.textContent = 'Loading voices...';
    loadingOption.disabled = true;
    voiceSelect.appendChild(loadingOption);

    try {
        // Fetch voices for English (en-US, en-GB, en-AU)
        const languageCodes = ['en-US', 'en-GB', 'en-AU'];
        const allVoices = [];
        const apiKey = getApiKey();

        for (const langCode of languageCodes) {
            try {
                const response = await fetch(`/api/voices?languageCode=${langCode}&apiKey=${encodeURIComponent(apiKey)}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.voices && Array.isArray(data.voices)) {
                        allVoices.push(...data.voices);
                    }
                } else if (response.status === 401 || response.status === 403) {
                    // API key invalid - delete and request new one
                    deleteApiKey();
                    showNotification('❌ API key 인증 실패. 업로드 화면에서 올바른 API key를 입력해주세요.', 'error');
                    throw new Error('API key authentication failed');
                }
            } catch (error) {
                console.error(`Error loading voices for ${langCode}:`, error);
                if (error.message.includes('authentication failed')) {
                    throw error;
                }
            }
        }

        // If no voices loaded, try without language filter
        if (allVoices.length === 0) {
            try {
                const apiKey = getApiKey();
                const response = await fetch(`/api/voices?apiKey=${encodeURIComponent(apiKey)}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.voices && Array.isArray(data.voices)) {
                        allVoices.push(...data.voices);
                    }
                } else if (response.status === 401 || response.status === 403) {
                    // API key invalid - delete and request new one
                    deleteApiKey();
                    showNotification('❌ API key 인증 실패. 업로드 화면에서 올바른 API key를 입력해주세요.', 'error');
                    throw new Error('API key authentication failed');
                }
            } catch (error) {
                console.error('Error loading voices:', error);
                if (error.message.includes('authentication failed')) {
                    throw error;
                }
            }
        }

        // Filter to en-US-Standard-*, en-GB-Standard-*, en-AU-Standard-* voices only and sort
        const englishVoices = allVoices.filter(voice => 
            voice.name && (
                voice.name.startsWith('en-US-Standard-') ||
                voice.name.startsWith('en-GB-Standard-') ||
                voice.name.startsWith('en-AU-Standard-')
            )
        ).sort((a, b) => {
            // Sort by language code first, then by name
            const langA = a.name.substring(0, 5); // "en-US", "en-GB", "en-AU"
            const langB = b.name.substring(0, 5);
            if (langA !== langB) return langA.localeCompare(langB);
            return a.name.localeCompare(b.name);
        });

        // Store voices
        googleVoicesList = englishVoices.map(voice => ({
            name: voice.name,
            description: formatVoiceDescription(voice),
            languageCode: voice.languageCodes[0] || 'en-US',
            ssmlGender: voice.ssmlGender,
            naturalSampleRateHertz: voice.naturalSampleRateHertz,
            model: voice.model || null  // Store model if available (required for some voices like Gemini)
        }));

        // Clear all options
        voiceSelect.innerHTML = '';
        
        // Add "Auto" option first
        const autoOption = document.createElement('option');
        autoOption.value = '';
        autoOption.textContent = 'Auto (Best English)';
        voiceSelect.appendChild(autoOption);

        // Add Google Cloud TTS voices
        googleVoicesList.forEach((voice) => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = voice.description;
            voiceSelect.appendChild(option);
        });

        // Set default
        const savedVoice = localStorage.getItem('selectedGoogleVoice');
        if (savedVoice) {
            const found = googleVoicesList.find(v => v.name === savedVoice);
            if (found) {
                voiceSelect.value = savedVoice;
                selectedVoice = found;
            }
        } else if (googleVoicesList.length > 0) {
            // Default to en-US-Neural2-D if available, otherwise first voice
            // default: en-US-Standard-F
            const defaultVoice = googleVoicesList.find(v => v.name === 'en-US-Standard-F') || googleVoicesList[0];
            voiceSelect.value = defaultVoice.name;
            selectedVoice = defaultVoice;
            localStorage.setItem('selectedGoogleVoice', defaultVoice.name);
        }

        voiceSelect.disabled = false;
    } catch (error) {
        console.error('Failed to load voices:', error);
        
        // Clear and add default option
        voiceSelect.innerHTML = '';
        const autoOption = document.createElement('option');
        autoOption.value = '';
        autoOption.textContent = 'Auto (Best English)';
        voiceSelect.appendChild(autoOption);
        
        voiceSelect.disabled = false;
        showNotification('⚠️ Failed to load voices. Using default.', 'warning');
    }
}

// Format voice description from API response
function formatVoiceDescription(voice) {
    const name = voice.name || '';
    const gender = voice.ssmlGender || '';
    const langCode = voice.languageCodes?.[0] || '';
    
    // Extract language and accent
    let langLabel = '';
    if (langCode.startsWith('en-US')) langLabel = 'US';
    else if (langCode.startsWith('en-GB')) langLabel = 'UK';
    else if (langCode.startsWith('en-AU')) langLabel = 'AU';
    else langLabel = langCode;
    
    // Extract gender
    const genderLabel = gender === 'FEMALE' ? 'Female' : gender === 'MALE' ? 'Male' : '';
    
    // Extract voice type from name (e.g., Neural2, WaveNet, Standard)
    let typeLabel = '';
    if (name.includes('Neural2')) typeLabel = 'Neural2';
    else if (name.includes('Neural')) typeLabel = 'Neural';
    else if (name.includes('WaveNet')) typeLabel = 'WaveNet';
    else if (name.includes('Standard')) typeLabel = 'Standard';
    
    // Build description
    const parts = [langLabel];
    if (genderLabel) parts.push(genderLabel);
    if (typeLabel) parts.push(typeLabel);
    
    // Add voice identifier (last letter)
    const voiceId = name.split('-').pop();
    if (voiceId) parts.push(`(${voiceId})`);
    
    return parts.join(' ');
}

// Stop all audio playback (both Google TTS and Web Speech API)
function stopAllAudio() {
    // Stop Google TTS audio
    if (audioElement) {
        try {
            audioElement.pause();
            // Remove all event listeners by cloning the element
            const src = audioElement.src;
            audioElement.src = '';
            audioElement.load(); // Reset the element
        } catch (e) {
            console.error('Error stopping audio:', e);
        }
        audioElement = null;
    }
    
    // Stop Web Speech API
    try {
        userCanceled = true; // Mark as user-initiated cancel
        window.speechSynthesis.cancel();
    } catch (e) {
        console.error('Error canceling speech synthesis:', e);
    }
    utterance = null;
    
    // Clear progress interval
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    // Reset progress
    currentProgress = 0;
    pausedCharIndex = 0;
    
    // Reset progress bar
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = '0%';
    }
}

// Load browser TTS voices (Web Speech API)
function loadBrowserVoices() {
    const voiceSelect = document.getElementById('voiceSelect');
    if (!voiceSelect) return;

    // Get voices from Web Speech API
    let voices = window.speechSynthesis.getVoices();
    
    // Some browsers need voices to be loaded asynchronously
    if (voices.length === 0) {
        // Wait for voices to load
        window.speechSynthesis.onvoiceschanged = () => {
            voices = window.speechSynthesis.getVoices();
            populateBrowserVoices(voices);
        };
        // Trigger voices loading
        const dummyUtterance = new SpeechSynthesisUtterance('');
        window.speechSynthesis.speak(dummyUtterance);
        window.speechSynthesis.cancel();
    } else {
        populateBrowserVoices(voices);
    }
}

// Populate browser voices in the select dropdown
function populateBrowserVoices(voices) {
    const voiceSelect = document.getElementById('voiceSelect');
    if (!voiceSelect) return;

    // Filter English voices
    let englishVoices = voices.filter(voice =>
        voice.lang.startsWith('en-')
    );

    // iOS Chrome: Filter to safe voices only
    if (isIOSChrome()) {
        const safeVoiceNames = ['Samantha', 'Aaron', 'Nicky', 'Fred', 'Victoria', 'Karen'];
        const filteredVoices = englishVoices.filter(voice =>
            safeVoiceNames.includes(voice.name) || !voice.localService
        );

        if (filteredVoices.length > 0) {
            englishVoices = filteredVoices;
            console.log(`[iOS Chrome] Voice list filtered to ${englishVoices.length} safe voices`);
        } else {
            console.warn('[iOS Chrome] No safe voices found in filter, using all available');
        }
    }

    // Sort voices
    englishVoices.sort((a, b) => {
        // Sort by language code first (en-US, en-GB, etc.)
        const langCompare = a.lang.localeCompare(b.lang);
        if (langCompare !== 0) return langCompare;
        // Then by name
        return a.name.localeCompare(b.name);
    });

    // Clear all options
    voiceSelect.innerHTML = '';

    // Add "Auto" option first
    const autoOption = document.createElement('option');
    autoOption.value = '';
    autoOption.textContent = 'Auto (Best English)';
    voiceSelect.appendChild(autoOption);

    // Add browser voices
    englishVoices.forEach((voice) => {
        const option = document.createElement('option');
        option.value = voice.name;
        
        // Format voice description
        const langCode = voice.lang;
        let langLabel = '';
        if (langCode.startsWith('en-US')) langLabel = 'US';
        else if (langCode.startsWith('en-GB')) langLabel = 'UK';
        else if (langCode.startsWith('en-AU')) langLabel = 'AU';
        else if (langCode.startsWith('en-CA')) langLabel = 'CA';
        else if (langCode.startsWith('en-IN')) langLabel = 'IN';
        else langLabel = langCode;
        
        const description = `${langLabel} - ${voice.name}${voice.default ? ' (Default)' : ''}`;
        option.textContent = description;
        option.dataset.voice = JSON.stringify({
            name: voice.name,
            lang: voice.lang,
            voice: voice
        });
        voiceSelect.appendChild(option);
    });

    // Set default
    const savedVoice = localStorage.getItem('selectedBrowserVoice');
    if (savedVoice) {
        const found = englishVoices.find(v => v.name === savedVoice);
        if (found) {
            voiceSelect.value = savedVoice;
            // Store voice name only, we'll find the voice object when needed
            selectedVoice = { name: found.name, isBrowserVoice: true };
        } else {
            // Saved voice not found, use auto
            voiceSelect.value = '';
            selectedVoice = null;
        }
    } else {
        // Default to first English voice or auto
        voiceSelect.value = '';
        selectedVoice = null;
    }

    voiceSelect.disabled = false;
}

// Change voice
function changeVoice() {
    const voiceSelect = document.getElementById('voiceSelect');
    const selectedName = voiceSelect.value;

    if (selectedName === '') {
        selectedVoice = null;
        if (currentTTSMode === 'google') {
            localStorage.removeItem('selectedGoogleVoice');
        } else {
            localStorage.removeItem('selectedBrowserVoice');
        }
    } else {
        if (currentTTSMode === 'google') {
            const voice = googleVoicesList.find(v => v.name === selectedName);
            if (voice) {
                selectedVoice = voice;
                localStorage.setItem('selectedGoogleVoice', voice.name);
            }
        } else {
            // Browser TTS
            const selectedOption = voiceSelect.options[voiceSelect.selectedIndex];
            if (selectedOption && selectedOption.dataset.voice) {
                const voiceData = JSON.parse(selectedOption.dataset.voice);
                // Store voice name only, we'll find the voice object when needed
                selectedVoice = { name: voiceData.name, isBrowserVoice: true };
                localStorage.setItem('selectedBrowserVoice', voiceData.name);
            }
        }
    }

    // If playing, stop current playback and restart with new voice
    if (isPlaying && !isPaused) {
        stopAllAudio();
        // Small delay to ensure cleanup is complete
        setTimeout(() => {
            playCurrentTrack();
        }, 100);
    }
}

// CSV Upload Handler
function handleCSVUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const csvContent = e.target.result;
        const pasteArea = document.getElementById('pasteArea');
        
        if (!pasteArea) {
            showNotification('❌ 텍스트 영역을 찾을 수 없습니다.', 'error');
            event.target.value = '';
            return;
        }

        // Parse CSV to remove header and format data only
        Papa.parse(csvContent, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                if (results.data.length === 0) {
                    showNotification('❌ CSV 파일에 유효한 데이터가 없습니다.', 'error');
                    event.target.value = '';
                    return;
                }

                // Convert to CSV format without header
                const csvWithoutHeader = results.data
                    .filter(row => row.english && row.korean)
                    .map(row => {
                        // Escape quotes and wrap in quotes if contains comma or quote
                        const english = row.english.trim();
                        const korean = row.korean.trim();
                        const needsQuotes = english.includes(',') || english.includes('"') || 
                                          korean.includes(',') || korean.includes('"');
                        
                        if (needsQuotes) {
                            const escapedEnglish = english.replace(/"/g, '""');
                            const escapedKorean = korean.replace(/"/g, '""');
                            return `"${escapedEnglish}","${escapedKorean}"`;
                        } else {
                            return `${english},${korean}`;
                        }
                    })
                    .join('\n');

                // Display CSV content without header in textarea
                pasteArea.value = csvWithoutHeader;
                showNotification('✅ CSV 파일을 불러왔습니다. 필요시 수정 후 "플레이리스트 생성" 버튼을 클릭하세요.');
                
                // Scroll to textarea
                pasteArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
                pasteArea.focus();
                
                // Reset file input to allow selecting the same file again
                event.target.value = '';
            },
            error: (error) => {
                showNotification('❌ CSV 파일을 읽는 중 오류가 발생했습니다.', 'error');
                console.error(error);
                event.target.value = '';
            }
        });
    };
    reader.onerror = () => {
        showNotification('❌ CSV 파일을 읽는 중 오류가 발생했습니다.', 'error');
        event.target.value = '';
    };
    reader.readAsText(file);
}

// Text Paste Handler
function parseText() {
    const text = document.getElementById('pasteArea').value.trim();
    if (!text) {
        showNotification('❌ 텍스트를 입력해주세요.', 'error');
        return;
    }

    // Check if text is CSV format (contains comma-separated values)
    const lines = text.split('\n').filter(line => line.trim());
    
    // Check if most lines contain commas (CSV format)
    // Note: textarea doesn't have header row, so we check for comma-separated format
    const linesWithCommas = lines.filter(line => {
        const trimmed = line.trim();
        return trimmed.includes(',') && (
            trimmed.startsWith('"') || // Quoted CSV
            trimmed.match(/^[^,]+,[^,]+$/) // Simple CSV without quotes
        );
    }).length;
    
    // Consider CSV if more than half of lines are CSV format
    // Also check if first line looks like CSV header (user might have pasted with header)
    const firstLine = lines[0] ? lines[0].trim().toLowerCase() : '';
    const hasCSVHeader = firstLine === 'english,korean' || firstLine === '"english","korean"';
    const isCSVFormat = hasCSVHeader || (linesWithCommas > 0 && linesWithCommas >= lines.length / 2);

    let parsedTracks = [];

    if (isCSVFormat) {
        // Parse as CSV using Papa.parse
        // Check if header exists, if so use header: true, otherwise use header: false
        const hasHeader = hasCSVHeader;
        
        try {
            Papa.parse(text, {
                header: hasHeader,
                skipEmptyLines: true,
                complete: (results) => {
                    if (hasHeader) {
                        // If header exists, use column names
                        parsedTracks = results.data
                            .filter(row => row.english && row.korean)
                            .map(row => ({
                                english: row.english.trim(),
                                korean: row.korean.trim()
                            }));
                    } else {
                        // If no header, use column indices (0 = english, 1 = korean)
                        parsedTracks = results.data
                            .filter(row => row[0] && row[1])
                            .map(row => ({
                                english: String(row[0]).trim(),
                                korean: String(row[1]).trim()
                            }));
                    }

                    if (parsedTracks.length > 0) {
                        loadPlaylist(parsedTracks);
                        showNotification(`✅ ${parsedTracks.length}개 트랙을 생성했습니다!`);
                        // Keep textarea content for editing
                    } else {
                        showNotification('❌ CSV 형식이 올바르지 않습니다.\n형식: english,korean 또는 "english","korean"', 'error');
                    }
                },
                error: (error) => {
                    showNotification('❌ CSV 파싱 중 오류가 발생했습니다.', 'error');
                    console.error(error);
                }
            });
        } catch (error) {
            showNotification('❌ CSV 파싱 중 오류가 발생했습니다.', 'error');
            console.error(error);
        }
    } else {
        // Parse as line-by-line format (legacy support)
        for (let i = 0; i < lines.length; i += 2) {
            if (lines[i] && lines[i + 1]) {
                parsedTracks.push({
                    english: lines[i].trim(),
                    korean: lines[i + 1].trim()
                });
            }
        }

        if (parsedTracks.length > 0) {
            loadPlaylist(parsedTracks);
            showNotification(`✅ ${parsedTracks.length}개 트랙을 생성했습니다!`);
            // Keep textarea content for editing
        } else {
            showNotification('❌ 올바른 형식으로 입력해주세요.\nCSV 형식: english,korean\n또는 줄 단위: 영어 문장 → 한국어 번역', 'error');
        }
    }
}

// Clipboard Handler
async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        document.getElementById('pasteArea').value = text;
        showNotification('✅ 클립보드에서 텍스트를 가져왔습니다!');
    } catch (err) {
        showNotification('❌ 클립보드 접근 권한이 필요합니다.', 'error');
        console.error(err);
    }
}

// Load Sample Data
function loadSampleData() {
    loadPlaylist(sampleTracks);
    showNotification('✅ 샘플 데이터를 불러왔습니다!');
}

// 전역 스코프에 명시적으로 노출 (HTML onclick 속성에서 사용)
window.loadSampleData = loadSampleData;

// Load Playlist
function loadPlaylist(newTracks) {
    tracks = newTracks;
    currentTrack = 0;
    renderPlaylist();
    showPlayerScreen();
    loadTrack(0);
}

// Render Playlist
function renderPlaylist() {
    const container = document.getElementById('playlistItems');
    container.innerHTML = '';

    tracks.forEach((track, index) => {
        const item = document.createElement('div');
        item.className = 'playlist-item';
        if (index === currentTrack) {
            item.classList.add('active');
        }

        const durationText = track.duration ? formatDurationForPlaylist(track.duration) : '';

        item.innerHTML = `
            <div class="playlist-number">${String(index + 1).padStart(2, '0')}</div>
            <div class="playlist-content">
                <div class="playlist-text">
                    <span>${track.english}</span>
                    ${durationText ? `<span class="playlist-duration">${durationText}</span>` : ''}
                </div>
                <div class="playlist-korean">${track.korean}</div>
            </div>
        `;

        item.addEventListener('click', () => {
            loadTrack(index);
        });

        container.appendChild(item);
    });

    document.getElementById('playlistCount').textContent = `${tracks.length} tracks`;
}

// Update playlist duration for a specific track
function updatePlaylistDuration(index, duration) {
    if (index < 0 || index >= tracks.length) return;
    
    const items = document.querySelectorAll('.playlist-item');
    if (items[index]) {
        const durationSpan = items[index].querySelector('.playlist-duration');
        if (durationSpan) {
            durationSpan.textContent = formatDurationForPlaylist(duration);
        } else {
            // Add duration if it doesn't exist
            const textDiv = items[index].querySelector('.playlist-text');
            if (textDiv) {
                const span = textDiv.querySelector('span');
                if (span) {
                    const durationSpan = document.createElement('span');
                    durationSpan.className = 'playlist-duration';
                    durationSpan.textContent = formatDurationForPlaylist(duration);
                    textDiv.appendChild(durationSpan);
                }
            }
        }
    }
}

// Load Track
function loadTrack(index) {
    if (index < 0 || index >= tracks.length) return;

    currentTrack = index;
    const track = tracks[currentTrack];

    // Update display
    document.getElementById('textEnglish').textContent = track.english;
    document.getElementById('textKorean').textContent = track.korean;
    document.getElementById('trackInfo').textContent = `${currentTrack + 1} of ${tracks.length}`;

    // Update playlist highlighting
    const playlistContainer = document.getElementById('playlistItems');
    const items = document.querySelectorAll('.playlist-item');
    
    items.forEach((item, i) => {
        if (i === currentTrack) {
            item.classList.add('active');
            // Scroll within playlist container only, not the entire page
            if (playlistContainer && items.length > 0) {
                // Use setTimeout to ensure DOM is fully updated
                setTimeout(() => {
                    // Get the first item to calculate relative positions
                    const firstItem = items[0];
                    const firstItemTop = firstItem.offsetTop;
                    const itemTop = item.offsetTop;
                    const itemHeight = item.offsetHeight;
                    const containerHeight = playlistContainer.clientHeight;
                    const currentScrollTop = playlistContainer.scrollTop;
                    
                    // Calculate item position relative to first item (which is at scrollTop 0)
                    const itemRelativeTop = itemTop - firstItemTop;
                    const itemRelativeBottom = itemRelativeTop + itemHeight;
                    
                    // Check if item is visible in current scroll position
                    const visibleTop = currentScrollTop;
                    const visibleBottom = currentScrollTop + containerHeight;
                    
                    // Scroll only if item is outside visible area
                    if (itemRelativeTop < visibleTop) {
                        // Item is above visible area - scroll to show it at top with padding
                        playlistContainer.scrollTo({
                            top: Math.max(0, itemRelativeTop - 8),
                            behavior: 'smooth'
                        });
                    } else if (itemRelativeBottom > visibleBottom) {
                        // Item is below visible area - scroll to show it at bottom with padding
                        playlistContainer.scrollTo({
                            top: Math.max(0, itemRelativeTop - containerHeight + itemHeight + 8),
                            behavior: 'smooth'
                        });
                    }
                }, 0);
            }
        } else {
            item.classList.remove('active');
        }
    });

    // Reset progress
    document.getElementById('progressFill').style.width = '0%';

    // Auto-play if already playing
    if (isPlaying) {
        playCurrentTrack();
    }
}

// Play/Pause Toggle
function togglePlay() {
    if (tracks.length === 0) {
        showNotification('❌ 플레이리스트가 비어있습니다.', 'error');
        return;
    }

    // iOS 초기화 추가
    if (isIOS() && !speechSynthesisInitialized) {
        initSpeechSynthesisForIOS();
    }

    if (isPlaying && !isPaused) {
        pauseCurrentTrack();
        document.getElementById('playBtn').textContent = '▶️';
        isPaused = true;
        isPlaying = false;
    } else if (isPaused) {
        resumeCurrentTrack();
        document.getElementById('playBtn').textContent = '⏸';
        isPaused = false;
        isPlaying = true;
    } else {
        document.getElementById('playBtn').textContent = '⏸';
        isPlaying = true;
        isPaused = false;
        playCurrentTrack(); // await 제거!
    }
}

// Play Current Track
// async function playCurrentTrack() {
//     // Stop any existing playback before starting new one
//     stopAllAudio();
    
//     // Small delay to ensure cleanup is complete
//     await new Promise(resolve => setTimeout(resolve, 50));
    
//     const mode = selectTTSMode();

//     if (mode === 'google') {
//         await playWithGoogleTTS();
//     } else {
//         playWithWebSpeechAPI();
//     }
// }

async function playCurrentTrack() {
    const mode = selectTTSMode();

    if (mode === 'google') {
        stopAllAudio();
        await new Promise(resolve => setTimeout(resolve, 50));
        await playWithGoogleTTS();
    } else {
        // Web Speech API - 동기 실행 필수!
        stopAllAudio();
        
        if (isIOS() && !speechSynthesisInitialized) {
            initSpeechSynthesisForIOS();
        }
        
        playWithWebSpeechAPI(); // await 없이 즉시 호출!
    }
}


// Play with Google Cloud TTS
async function playWithGoogleTTS() {
    try {
        // Check if API key is available
        if (!hasApiKey()) {
            showNotification('⚠️ API key가 필요합니다. 업로드 화면에서 API key를 입력해주세요.', 'warning');
            return;
        }

        const track = tracks[currentTrack];
        const voiceName = selectedVoice?.name || 'en-US-Standard-F';
        const languageCode = selectedVoice?.languageCode || 'en-US';
        const model = selectedVoice?.model || null;
        const cacheKey = generateCacheKey(track.english, voiceName);
        const apiKey = getApiKey();

        // Check cache first
        console.log('[TTS Cache] Checking cache for:', {
            text: track.english.substring(0, 50) + (track.english.length > 50 ? '...' : ''),
            voice: voiceName,
            cacheKey: cacheKey.substring(0, 16) + '...'
        });
        
        let cached = await getCachedAudio(cacheKey);

        if (!cached) {
            // Not in cache, fetch from API
            console.log('[TTS Cache] ❌ Cache MISS - Fetching from API');
            console.log('[TTS API] Calling Google Cloud TTS API...', {
                textLength: track.english.length,
                voice: voiceName,
                languageCode: languageCode,
                speed: playbackSpeed
            });
            
            showLoadingState();
            const apiStartTime = performance.now();

            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: track.english,
                    voice: voiceName,
                    languageCode: languageCode,
                    model: model,
                    speed: playbackSpeed,
                    apiKey: apiKey
                })
            });

            if (!response.ok) {
                const error = await response.json();
                console.error('[TTS API] ❌ API Error:', error);
                throw new Error(error.error || 'TTS API error');
            }

            const data = await response.json();
            const apiEndTime = performance.now();
            const apiDuration = (apiEndTime - apiStartTime).toFixed(2);

            console.log('[TTS API] ✅ API Call Success', {
                duration: `${apiDuration}ms`,
                characters: data.characters,
                estimatedDuration: `${(data.estimatedDuration / 1000).toFixed(2)}s`
            });

            // Convert base64 to Blob
            const audioBlob = base64ToBlob(data.audio);

            // Store in cache
            await storeAudioInCache(cacheKey, audioBlob, data.estimatedDuration / 1000, voiceName, track.english);

            cached = { audioBlob, duration: data.estimatedDuration / 1000 };

            hideLoadingState();
        } else {
            console.log('[TTS Cache] ✅ Cache HIT', {
                size: `${(cached.audioBlob.size / 1024).toFixed(2)} KB`,
                duration: `${cached.duration.toFixed(2)}s`,
                age: `${Math.round((Date.now() - cached.createdAt) / (1000 * 60 * 60))} hours ago`
            });
            
            // Don't store estimated duration from cache - wait for actual audio metadata
            // The actual duration will be set in the loadedmetadata event handler
        }

        // Stop existing audio (both Google TTS and Web Speech API)
        stopAllAudio();

        // Create new Audio element
        const blobURL = URL.createObjectURL(cached.audioBlob);

        // Clean up old blob URLs
        if (cachedBlobURLs.has(currentTrack)) {
            URL.revokeObjectURL(cachedBlobURLs.get(currentTrack));
        }
        cachedBlobURLs.set(currentTrack, blobURL);

        audioElement = new Audio(blobURL);
        audioElement.playbackRate = playbackSpeed;

        // Store reference to current audio element for event listeners
        const currentAudioElement = audioElement;

        // Event: metadata loaded (we get real duration!)
        // Note: audioElement.duration is always at 1.0x speed, regardless of playbackRate
        audioElement.addEventListener('loadedmetadata', async () => {
            // Check if this is still the current audio element
            if (audioElement !== currentAudioElement || !audioElement) return;
            
            // Get duration at 1.0x speed (playbackRate doesn't affect this property)
            const duration = audioElement.duration;
            
            console.log('[TTS Duration] Actual audio duration loaded', {
                duration: `${duration.toFixed(2)}s`,
                formatted: formatTime(duration)
            });
            
            // Store duration in track (always at 1.0x speed for playlist display)
            if (tracks[currentTrack]) {
                const oldDuration = tracks[currentTrack].duration;
                tracks[currentTrack].duration = duration; // 1.0x 기준 duration
                
                if (oldDuration && Math.abs(oldDuration - duration) > 0.1) {
                    console.log('[TTS Duration] Duration updated', {
                        old: `${oldDuration.toFixed(2)}s`,
                        new: `${duration.toFixed(2)}s`,
                        difference: `${(duration - oldDuration).toFixed(2)}s`
                    });
                }
            }
            
            // Update playlist display with duration (always shows 1.0x speed)
            updatePlaylistDuration(currentTrack, duration);
            
            // Update cache with actual duration (for future cache hits)
            const track = tracks[currentTrack];
            if (track) {
                const voiceName = selectedVoice?.name || 'en-US-Standard-F';
                const cacheKey = generateCacheKey(track.english, voiceName);
                await updateCacheDuration(cacheKey, duration);
            }
            
            const timeDisplay = document.getElementById('timeDisplay');
            if (timeDisplay) {
                timeDisplay.textContent = `00.00s / ${formatDurationForPlaylist(duration)}`;
            }
        });

        // Event: time update (smooth progress!)
        audioElement.addEventListener('timeupdate', () => {
            // Check if this is still the current audio element
            if (audioElement !== currentAudioElement || !audioElement) return;
            
            try {
                const current = audioElement.currentTime;
                const total = audioElement.duration;
                const progress = (current / total) * 100;

                const progressFill = document.getElementById('progressFill');
                if (progressFill) {
                    progressFill.style.width = `${progress}%`;
                }
                
                const timeDisplay = document.getElementById('timeDisplay');
                if (timeDisplay) {
                    timeDisplay.textContent = `${formatDurationForPlaylist(current)} / ${formatDurationForPlaylist(total)}`;
                }
            } catch (e) {
                // Audio element was removed, ignore
                console.warn('Audio element removed during timeupdate:', e);
            }
        });

        // Event: ended
        audioElement.addEventListener('ended', () => {
            // Check if this is still the current audio element
            if (audioElement !== currentAudioElement) return;
            handleTrackEnd();
        });

        // Event: error
        audioElement.addEventListener('error', (e) => {
            // Check if this is still the current audio element
            if (audioElement !== currentAudioElement) return;
            
            const errorDetails = {
                errorCode: audioElement.error?.code,
                errorMessage: audioElement.error?.message,
                errorName: audioElement.error?.name,
                src: audioElement.src?.substring(0, 100),
                currentTrack: currentTrack,
                trackText: tracks[currentTrack]?.english?.substring(0, 50),
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                isOnline: navigator.onLine,
                ttsMode: currentTTSMode
            };
            
            console.error('Audio playback error:', errorDetails);
            addDebugLog(`TTS Error [${errorDetails.errorCode}]: ${errorDetails.errorMessage || 'Unknown error'}`, 'error');
            addDebugLog(`Track: ${errorDetails.trackText}`, 'error');
            addDebugLog(`Platform: ${errorDetails.platform}`, 'error');
            
            hideLoadingState();
            
            // Stop the failed audio element
            if (audioElement === currentAudioElement) {
                try {
                    audioElement.pause();
                    audioElement.src = '';
                } catch (err) {
                    console.error('Error cleaning up failed audio:', err);
                }
                audioElement = null;
            }
            
            showNotification('❌ Audio playback error. Switching to browser TTS.', 'error');
            
            // Small delay to ensure cleanup is complete before fallback
            setTimeout(() => {
                playWithWebSpeechAPI();
            }, 100);
        });

        // Play
        await audioElement.play();

    } catch (error) {
        console.error('Google TTS Error:', error);
        hideLoadingState();

        // Stop any existing audio before fallback
        stopAllAudio();

        if (error.message.includes('authentication failed')) {
            // API key issue - already handled above
            showNotification('❌ API key authentication failed. Please enter a valid API key.', 'error');
        } else if (error.message.includes('Quota exceeded') || error.message.includes('429')) {
            showNotification('⚠️ Monthly quota exceeded. Switching to browser TTS.', 'warning');
            // Small delay to ensure cleanup is complete before fallback
            setTimeout(() => {
                playWithWebSpeechAPI();
            }, 100);
        } else if (!navigator.onLine) {
            showNotification('📵 Offline. Using browser TTS.', 'info');
            // Small delay to ensure cleanup is complete before fallback
            setTimeout(() => {
                playWithWebSpeechAPI();
            }, 100);
        } else {
            showNotification('❌ TTS error. Using browser TTS.', 'error');
            // Small delay to ensure cleanup is complete before fallback
            setTimeout(() => {
                playWithWebSpeechAPI();
            }, 100);
        }
    }
}

// Track if user explicitly canceled
let userCanceled = false;

// iOS retry counter to prevent infinite recursion
let iosRetryCount = 0;
const MAX_IOS_RETRIES = 3;

// Detect iOS
function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

// Detect iOS Chrome specifically
function isIOSChrome() {
    return isIOS() && /CriOS/.test(navigator.userAgent);
}

// Initialize speech synthesis for iOS (call on first user interaction)
// function initSpeechSynthesis() {
//     if (isIOS() && !speechSynthesisInitialized) {
//         try {
//             const dummyUtterance = new SpeechSynthesisUtterance('');
//             dummyUtterance.volume = 0;
//             window.speechSynthesis.speak(dummyUtterance);
//             window.speechSynthesis.cancel();
//             speechSynthesisInitialized = true;
//             addDebugLog('Speech synthesis initialized for iOS', 'log');
//         } catch (e) {
//             console.error('Failed to initialize speech synthesis:', e);
//         }
//     }
// }

// initSpeechSynthesis() 함수를 이것으로 교체
function initSpeechSynthesisForIOS() {
    if (!isIOS() || speechSynthesisInitialized) return;
    
    try {
        console.log('[iOS Fix] Initializing Speech Synthesis...');
        
        const dummyUtterance = new SpeechSynthesisUtterance('');
        dummyUtterance.volume = 0;
        
        let voices = window.speechSynthesis.getVoices();
        if (voices.length === 0) {
            window.speechSynthesis.onvoiceschanged = () => {
                voices = window.speechSynthesis.getVoices();
                console.log('[iOS Fix] Voices loaded:', voices.length);
                speechSynthesisReady = true;
            };
        } else {
            speechSynthesisReady = true;
        }
        
        window.speechSynthesis.speak(dummyUtterance);
        window.speechSynthesis.cancel();
        
        speechSynthesisInitialized = true;
        console.log('[iOS Fix] Speech Synthesis initialized');
    } catch (e) {
        console.error('[iOS Fix] Failed to initialize:', e);
    }
}

// Play with Web Speech API (fallback)
function playWithWebSpeechAPI() {
    // iOS 초기화 체크 추가
    if (isIOS() && !speechSynthesisInitialized) {
        initSpeechSynthesisForIOS();
    }

    // Stop any existing speech
    userCanceled = false; // Reset cancel flag
    window.speechSynthesis.cancel();

    const track = tracks[currentTrack];

    // iOS 워크어라운드: cancel 후 지연 필요 (150ms → 300ms로 증가)
    const iosDelay = isIOS() ? 300 : 0;
    
    setTimeout(() => {
        // voices 로딩 체크 추가
        if (isIOS() && !speechSynthesisReady) {
            console.warn('[iOS Fix] Voices not ready yet, waiting...');
            setTimeout(() => playWithWebSpeechAPI(), 200);
            return;
        }

        utterance = new SpeechSynthesisUtterance(track.english);

        // Configure speech
        utterance.lang = 'en-US';
        utterance.rate = playbackSpeed;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Set selected voice if available (with validation)
        const voices = window.speechSynthesis.getVoices();

        // iOS Chrome: Filter out problematic voices that appear in list but don't work
        let availableVoices = voices;
        if (isIOSChrome()) {
            // iOS Chrome safe voices (tested to work reliably)
            const safeVoiceNames = ['Samantha', 'Aaron', 'Nicky', 'Fred', 'Victoria', 'Karen'];
            availableVoices = voices.filter(voice => {
                // Allow safe voices or any Google/network voices
                return safeVoiceNames.includes(voice.name) || !voice.localService;
            });

            if (availableVoices.length > 0) {
                addDebugLog(`[iOS Chrome] Filtered to ${availableVoices.length} safe voices`, 'log');
            } else {
                // Fallback: use all voices if filtering removed everything
                addDebugLog('[iOS Chrome] No safe voices found, using all available', 'warn');
                availableVoices = voices;
            }
        }

        if (selectedVoice) {
            if (selectedVoice.isBrowserVoice) {
                // Browser TTS - find voice by name in available voices
                const matchingVoice = availableVoices.find(voice => voice.name === selectedVoice.name);
                if (matchingVoice) {
                    utterance.voice = matchingVoice;
                    addDebugLog(`Using selected voice: ${matchingVoice.name} (${matchingVoice.localService ? 'local' : 'network'})`, 'log');
                } else {
                    // Voice not available (filtered out on iOS Chrome), use fallback
                    addDebugLog(`Selected voice not available: ${selectedVoice.name}`, 'warn');
                    if (isIOSChrome()) {
                        addDebugLog('[iOS Chrome] Switching to safe fallback voice', 'warn');
                    }
                }
            } else if (selectedVoice.name) {
                // Google TTS - find matching browser voice if available
                const matchingVoice = availableVoices.find(voice =>
                    voice.name === selectedVoice.name ||
                    voice.lang.startsWith('en-')
                );
                if (matchingVoice) {
                    utterance.voice = matchingVoice;
                    addDebugLog(`Using fallback voice: ${matchingVoice.name}`, 'log');
                }
            }
        }

        // If no voice set, auto-select best English voice from available voices
        if (!utterance.voice) {
            // iOS Chrome: Prefer "Samantha" as it's most reliable
            let englishVoice;
            if (isIOSChrome()) {
                englishVoice = availableVoices.find(voice => voice.name === 'Samantha')
                    || availableVoices.find(voice => voice.lang.startsWith('en-') && voice.localService)
                    || availableVoices.find(voice => voice.lang.startsWith('en-'));
            } else {
                // Other platforms: prefer local service voices
                englishVoice = availableVoices.find(voice =>
                    voice.lang.startsWith('en-') && voice.localService
                ) || availableVoices.find(voice => voice.lang.startsWith('en-'));
            }

            if (englishVoice) {
                utterance.voice = englishVoice;
                addDebugLog(`Auto-selected voice: ${englishVoice.name} (${englishVoice.localService ? 'local' : 'network'})`, 'log');
            } else {
                addDebugLog('No English voice found, using default', 'warn');
            }
        }

        // Reset progress
        currentProgress = 0;
        pausedCharIndex = 0; // Reset pause position

        // Estimate duration
        const estimatedDuration = (track.english.length * 150) / playbackSpeed;

        // Track progress with onboundary
        utterance.onboundary = (event) => {
            if (event.charIndex !== undefined) {
                // Reset retry counter on first successful boundary event (재생 성공)
                if (event.charIndex === 0 && iosRetryCount > 0) {
                    iosRetryCount = 0;
                    addDebugLog('Playback started successfully, retry counter reset', 'log');
                }

                const textLength = track.english.length;
                pausedCharIndex = event.charIndex; // Save current position for pause/resume
                currentProgress = (event.charIndex / textLength) * 100;
                document.getElementById('progressFill').style.width = currentProgress + '%';

                const elapsed = (currentProgress / 100) * estimatedDuration / 1000;
                document.getElementById('timeDisplay').textContent =
                    `${formatDurationForPlaylist(elapsed)} / ${formatDurationForPlaylist(estimatedDuration / 1000)}`;
            }
        };

        // Event handlers
        utterance.onend = handleTrackEnd;

    utterance.onerror = (error) => {
        // 'interrupted' is a normal cancellation, not a real error
        if (error.error === 'interrupted') {
            // This happens when cancel() is called or new utterance starts
            // This is expected behavior, so we can ignore it
            return;
        }
        
        // Extract detailed error information
        const errorDetails = {
            error: error.error,
            type: error.type,
            message: error.message,
            charIndex: error.charIndex,
            elapsedTime: error.elapsedTime,
            name: error.name,
            utteranceText: utterance.text?.substring(0, 50),
            utteranceLang: utterance.lang,
            utteranceVoice: utterance.voice?.name,
            utteranceRate: utterance.rate,
            utterancePitch: utterance.pitch,
            utteranceVolume: utterance.volume,
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            isOnline: navigator.onLine,
            speechSynthesisSpeaking: window.speechSynthesis.speaking,
            speechSynthesisPending: window.speechSynthesis.pending,
            speechSynthesisPaused: window.speechSynthesis.paused,
            availableVoices: window.speechSynthesis.getVoices().length,
            isPlaying: isPlaying,
            isPaused: isPaused,
            userCanceled: userCanceled
        };
        
        // Log detailed error information
        console.error('Speech error details:', errorDetails);
        addDebugLog(`Speech Error: ${error.error || 'Unknown'}`, 'error');
        addDebugLog(`Error Type: ${error.type || 'N/A'}`, 'error');
        addDebugLog(`Message: ${error.message || 'N/A'}`, 'error');
        addDebugLog(`Elapsed Time: ${error.elapsedTime?.toFixed(2)}s`, 'error');
        addDebugLog(`Char Index: ${error.charIndex}`, 'error');
        addDebugLog(`Text: ${errorDetails.utteranceText}`, 'error');
        addDebugLog(`Voice: ${errorDetails.utteranceVoice || 'Auto'}`, 'error');
        addDebugLog(`Platform: ${errorDetails.platform}`, 'error');
        addDebugLog(`Available Voices: ${errorDetails.availableVoices}`, 'error');
        addDebugLog(`User Canceled: ${userCanceled}`, 'error');
        addDebugLog(`Is Playing: ${isPlaying}`, 'error');
        
        // iOS에서 'canceled' 오류가 예상치 못하게 발생하는 경우 처리
        // 재생이 시작되지 않고 취소된 경우 (charIndex === 0)에만 재시도
        if (error.error === 'canceled' && !userCanceled && isPlaying && error.charIndex === 0) {
            if (iosRetryCount < MAX_IOS_RETRIES) {
                iosRetryCount++;
                addDebugLog(`iOS canceled error - retry ${iosRetryCount}/${MAX_IOS_RETRIES}`, 'warn');
                // iOS에서는 더 긴 지연이 필요할 수 있음
                const retryDelay = isIOS() ? 500 : 500;
                setTimeout(() => {
                    if (isPlaying && !isPaused) {
                        addDebugLog('Retrying speech synthesis...', 'warn');
                        playWithWebSpeechAPI();
                    }
                }, retryDelay);
                return; // 재시도 중이므로 상태를 변경하지 않음
            } else {
                addDebugLog('Max error retries reached', 'error');
                showNotification('❌ TTS 재생 실패. Google Cloud TTS를 사용하거나 브라우저를 새로고침해주세요.', 'error');
                iosRetryCount = 0; // Reset counter
            }
        }
        
        // 다른 오류나 사용자가 취소한 경우
        showNotification('❌ 음성 재생 중 오류가 발생했습니다.', 'error');
        isPlaying = false;
        isPaused = false;
        document.getElementById('playBtn').textContent = '▶️';
    };

        // Speak
        window.speechSynthesis.speak(utterance);

        // iOS: 재생 시작 확인 (무한 재귀 방지 로직 추가)
        if (isIOS()) {
            setTimeout(() => {
                if (!window.speechSynthesis.speaking && !window.speechSynthesis.pending) {
                    if (iosRetryCount < MAX_IOS_RETRIES) {
                        iosRetryCount++;
                        console.warn(`[iOS Fix] Speech did not start, retrying... (${iosRetryCount}/${MAX_IOS_RETRIES})`);
                        addDebugLog(`Retry attempt ${iosRetryCount}/${MAX_IOS_RETRIES}`, 'warn');
                        playWithWebSpeechAPI();
                    } else {
                        console.error('[iOS Fix] Max retries reached, stopping playback');
                        addDebugLog('Max retries reached, playback failed', 'error');
                        showNotification('❌ TTS 재생 시작 실패. 브라우저를 새로고침하거나 다른 음성을 선택해보세요.', 'error');
                        isPlaying = false;
                        isPaused = false;
                        document.getElementById('playBtn').textContent = '▶️';
                        iosRetryCount = 0; // Reset counter
                    }
                } else {
                    // 재생 성공 시 카운터 리셋
                    iosRetryCount = 0;
                }
            }, 200); // 100ms → 200ms로 증가
        }

        // Update time display
        const seconds = Math.ceil(estimatedDuration / 1000);
        document.getElementById('timeDisplay').textContent =
            `00.00s / ${formatDurationForPlaylist(seconds)}`;
    }, iosDelay);
}

// Handle track end
function handleTrackEnd() {
    if (!isPlaying && !isPaused) return;

    // Complete progress bar
    document.getElementById('progressFill').style.width = '100%';
    currentProgress = 0;
    isPaused = false;

    if (repeatMode === 'one') {
        // Repeat current track
        setTimeout(() => playCurrentTrack(), 500);
    } else if (repeatMode === 'all') {
        // Move to next or loop
        if (currentTrack < tracks.length - 1) {
            loadTrack(currentTrack + 1);
        } else {
            loadTrack(0);
        }
    } else {
        // Normal mode
        if (currentTrack < tracks.length - 1) {
            loadTrack(currentTrack + 1);
        } else {
            isPlaying = false;
            isPaused = false;
            document.getElementById('playBtn').textContent = '▶️';
        }
    }
}

// Pause Current Track
function pauseCurrentTrack() {
    if (audioElement) {
        // Google TTS: perfect pause!
        audioElement.pause();
    } else {
        // Web Speech API fallback
        // Try to use pause() if available, otherwise cancel and save position
        if (typeof window.speechSynthesis.pause === 'function') {
            try {
                window.speechSynthesis.pause();
            } catch (e) {
                // If pause fails, cancel and save position
                console.warn('speechSynthesis.pause() failed, using cancel:', e);
                window.speechSynthesis.cancel();
            }
        } else {
            // pause() not available, cancel and save position
            window.speechSynthesis.cancel();
        }
    }

    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

// Resume Current Track
function resumeCurrentTrack() {
    if (audioElement) {
        // Google TTS: perfect resume from exact position!
        audioElement.play();
    } else {
        // Web Speech API fallback
        // Try to use resume() if available and paused
        if (typeof window.speechSynthesis.resume === 'function' && window.speechSynthesis.paused) {
            try {
                window.speechSynthesis.resume();
            } catch (e) {
                // If resume fails, restart from saved position
                console.warn('speechSynthesis.resume() failed, restarting from position:', e);
                resumeFromPosition();
            }
        } else {
            // resume() not available or not paused, restart from saved position
            resumeFromPosition();
        }
    }
}

// Resume Web Speech API from saved position
function resumeFromPosition() {
    const track = tracks[currentTrack];
    if (!track || pausedCharIndex >= track.english.length) {
        // If at end or no saved position, restart from beginning
        playCurrentTrack();
        return;
    }

    // Get remaining text from paused position
    const remainingText = track.english.substring(pausedCharIndex);
    if (!remainingText.trim()) {
        // No remaining text, move to next track
        handleTrackEnd();
        return;
    }

    // Stop any existing speech
    window.speechSynthesis.cancel();

    // iOS 워크어라운드: cancel 후 지연 필요 (100ms → 300ms로 증가)
    const iosDelay = isIOS() ? 300 : 0;
    
    setTimeout(() => {
        // Create new utterance with remaining text
        utterance = new SpeechSynthesisUtterance(remainingText);

        // Configure speech
        utterance.lang = 'en-US';
        utterance.rate = playbackSpeed;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Set selected voice if available (with validation)
        const voices = window.speechSynthesis.getVoices();

        if (selectedVoice) {
            if (selectedVoice.isBrowserVoice) {
                // Browser TTS - find voice by name
                const matchingVoice = voices.find(voice => voice.name === selectedVoice.name);
                if (matchingVoice) {
                    utterance.voice = matchingVoice;
                } else {
                    addDebugLog(`Selected voice not found (resume): ${selectedVoice.name}`, 'warn');
                }
            } else if (selectedVoice.name) {
                // Google TTS - find matching browser voice if available
                const matchingVoice = voices.find(voice =>
                    voice.name === selectedVoice.name ||
                    voice.lang.startsWith('en-')
                );
                if (matchingVoice) {
                    utterance.voice = matchingVoice;
                }
            }
        }

        // If no voice set, auto-select best English voice
        if (!utterance.voice) {
            // iOS: 로컬 voice 우선 선택 (네트워크 음성은 문제가 많음)
            const englishVoice = voices.find(voice =>
                voice.lang.startsWith('en-') && voice.localService
            ) || voices.find(voice => voice.lang.startsWith('en-'));

            if (englishVoice) {
                utterance.voice = englishVoice;
            }
        }

        // Calculate remaining duration
        const totalLength = track.english.length;
        const remainingLength = remainingText.length;
        const estimatedTotalDuration = (totalLength * 150) / playbackSpeed;
        const estimatedRemainingDuration = (remainingLength * 150) / playbackSpeed;
        const elapsedDuration = ((pausedCharIndex / totalLength) * estimatedTotalDuration) / 1000;

        // Track progress with onboundary (adjust for resume position)
        utterance.onboundary = (event) => {
            if (event.charIndex !== undefined) {
                const actualCharIndex = pausedCharIndex + event.charIndex;
                const textLength = track.english.length;
                pausedCharIndex = actualCharIndex; // Update saved position
                currentProgress = (actualCharIndex / textLength) * 100;
                document.getElementById('progressFill').style.width = currentProgress + '%';

                const elapsed = elapsedDuration + ((event.charIndex / remainingLength) * estimatedRemainingDuration) / 1000;
                const total = estimatedTotalDuration / 1000;
                document.getElementById('timeDisplay').textContent =
                    `${formatDurationForPlaylist(elapsed)} / ${formatDurationForPlaylist(total)}`;
            }
        };

        // Event handlers
        utterance.onend = handleTrackEnd;

        utterance.onerror = (error) => {
            // 'interrupted' is a normal cancellation, not a real error
            if (error.error === 'interrupted') {
                // This happens when cancel() is called or new utterance starts
                // This is expected behavior, so we can ignore it
                return;
            }
            
            // Extract detailed error information
            const errorDetails = {
                error: error.error,
                type: error.type,
                message: error.message,
                charIndex: error.charIndex,
                elapsedTime: error.elapsedTime,
                name: error.name,
                utteranceText: utterance.text?.substring(0, 50),
                utteranceLang: utterance.lang,
                utteranceVoice: utterance.voice?.name,
                utteranceRate: utterance.rate,
                utterancePitch: utterance.pitch,
                utteranceVolume: utterance.volume,
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                isOnline: navigator.onLine,
                speechSynthesisSpeaking: window.speechSynthesis.speaking,
                speechSynthesisPending: window.speechSynthesis.pending,
                speechSynthesisPaused: window.speechSynthesis.paused,
                availableVoices: window.speechSynthesis.getVoices().length,
                isPlaying: isPlaying,
                isPaused: isPaused,
                userCanceled: userCanceled
            };
            
            // Log detailed error information
            console.error('Speech error details (resume):', errorDetails);
            addDebugLog(`Speech Error (Resume): ${error.error || 'Unknown'}`, 'error');
            addDebugLog(`Error Type: ${error.type || 'N/A'}`, 'error');
            addDebugLog(`Message: ${error.message || 'N/A'}`, 'error');
            addDebugLog(`Elapsed Time: ${error.elapsedTime?.toFixed(2)}s`, 'error');
            addDebugLog(`Char Index: ${error.charIndex}`, 'error');
            addDebugLog(`Text: ${errorDetails.utteranceText}`, 'error');
            addDebugLog(`Voice: ${errorDetails.utteranceVoice || 'Auto'}`, 'error');
            addDebugLog(`Platform: ${errorDetails.platform}`, 'error');
            addDebugLog(`Available Voices: ${errorDetails.availableVoices}`, 'error');
            addDebugLog(`User Canceled: ${userCanceled}`, 'error');
            addDebugLog(`Is Playing: ${isPlaying}`, 'error');
            
            // iOS에서 'canceled' 오류가 예상치 못하게 발생하는 경우 처리
            // 재생이 시작되지 않고 취소된 경우 (charIndex === 0)에만 재시도
            if (error.error === 'canceled' && !userCanceled && isPlaying && error.charIndex === 0) {
                if (iosRetryCount < MAX_IOS_RETRIES) {
                    iosRetryCount++;
                    addDebugLog(`iOS canceled error (resume) - retry ${iosRetryCount}/${MAX_IOS_RETRIES}`, 'warn');
                    // iOS에서는 더 긴 지연이 필요할 수 있음
                    const retryDelay = isIOS() ? 500 : 500;
                    setTimeout(() => {
                        if (isPlaying && !isPaused) {
                            addDebugLog('Retrying speech synthesis (resume)...', 'warn');
                            resumeFromPosition();
                        }
                    }, retryDelay);
                    return; // 재시도 중이므로 상태를 변경하지 않음
                } else {
                    addDebugLog('Max error retries reached (resume)', 'error');
                    showNotification('❌ TTS 재생 재개 실패. Google Cloud TTS를 사용하거나 브라우저를 새로고침해주세요.', 'error');
                    iosRetryCount = 0; // Reset counter
                }
            }
            
            // 다른 오류나 사용자가 취소한 경우
            showNotification('❌ 음성 재생 중 오류가 발생했습니다.', 'error');
            isPlaying = false;
            isPaused = false;
            document.getElementById('playBtn').textContent = '▶️';
        };

        // Speak remaining text
        window.speechSynthesis.speak(utterance);
    }, iosDelay);
}

// Animate Progress
function animateProgress(duration) {
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    const progressBar = document.getElementById('progressFill');
    let progress = 0;
    const increment = 100 / (duration / 100);

    progressInterval = setInterval(() => {
        progress += increment;
        if (progress >= 100) {
            progress = 100;
            clearInterval(progressInterval);
        }
        progressBar.style.width = progress + '%';
    }, 100);
}

// First Track
function firstTrack() {
    if (tracks.length === 0) return;
    loadTrack(0);
    if (isPlaying) {
        playCurrentTrack();
    }
}

// Previous Track
function prevTrack() {
    if (currentTrack > 0) {
        loadTrack(currentTrack - 1);
        if (isPlaying) {
            playCurrentTrack();
        }
    } else if (repeatMode === 'all') {
        loadTrack(tracks.length - 1);
        if (isPlaying) {
            playCurrentTrack();
        }
    }
}

// Next Track
function nextTrack() {
    if (currentTrack < tracks.length - 1) {
        loadTrack(currentTrack + 1);
        if (isPlaying) {
            playCurrentTrack();
        }
    } else {
        // 마지막 문장에서 다음 문장 버튼을 누르면 첫 문장으로 이동
        loadTrack(0);
        if (isPlaying) {
            playCurrentTrack();
        }
    }
}

// Last Track
function lastTrack() {
    if (tracks.length === 0) return;
    loadTrack(tracks.length - 1);
    if (isPlaying) {
        playCurrentTrack();
    }
}

// Set Speed
function setSpeed(speed) {
    playbackSpeed = speed;

    // Update UI
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // If using Google TTS, change speed instantly (no restart needed!)
    if (audioElement && isPlaying && !isPaused) {
        audioElement.playbackRate = speed;
    }
    // If using Web Speech API, need to restart
    else if (isPlaying && !isPaused && !audioElement) {
        playCurrentTrack();
    }
}

// Set Repeat Mode
function setRepeat(mode) {
    const btn = event.target;
    
    if (repeatMode === mode) {
        // Toggle off
        repeatMode = 'none';
        btn.classList.remove('active');
    } else {
        // Set new mode
        repeatMode = mode;
        document.querySelectorAll('.repeat-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
}

// Show/Hide Screens
function showPlayerScreen() {
    document.getElementById('uploadCard').style.display = 'none';
    document.getElementById('playerCard').style.display = 'block';
}

function showUploadScreen() {
    // Stop playback
    if (isPlaying) {
        togglePlay();
    }
    
    document.getElementById('playerCard').style.display = 'none';
    document.getElementById('uploadCard').style.display = 'block';
    
    // Show "재생" button if tracks exist
    const goToPlayerBtn = document.getElementById('goToPlayerBtn');
    if (goToPlayerBtn) {
        goToPlayerBtn.style.display = tracks.length > 0 ? 'block' : 'none';
    }
}

// Save Playlist
function savePlaylist() {
    if (tracks.length === 0) {
        showNotification('❌ 저장할 플레이리스트가 없습니다.', 'error');
        return;
    }

    const name = prompt('플레이리스트 이름을 입력하세요:', `Playlist ${new Date().toLocaleDateString()}`);
    if (!name) return;

    const playlists = JSON.parse(localStorage.getItem('playlists') || '{}');
    playlists[name] = tracks;
    localStorage.setItem('playlists', JSON.stringify(playlists));

    showNotification(`✅ "${name}" 저장 완료!`);
    loadSavedPlaylists();
}

// Load Saved Playlists
function loadSavedPlaylists() {
    const playlists = JSON.parse(localStorage.getItem('playlists') || '{}');
    const container = document.getElementById('playlistList');
    const savedSection = document.getElementById('savedPlaylists');

    if (Object.keys(playlists).length === 0) {
        savedSection.style.display = 'none';
        return;
    }

    savedSection.style.display = 'block';
    container.innerHTML = '';

    Object.entries(playlists).forEach(([name, tracks]) => {
        const item = document.createElement('div');
        item.className = 'saved-playlist-item';
        item.innerHTML = `
            <div>
                <div class="saved-playlist-name">${name}</div>
                <div class="saved-playlist-count">${tracks.length} tracks</div>
            </div>
            <button class="saved-playlist-delete" onclick="deletePlaylist('${name}')">🗑️</button>
        `;
        
        item.addEventListener('click', (e) => {
            if (e.target.classList.contains('saved-playlist-delete')) return;
            loadPlaylist(tracks);
            showNotification(`✅ "${name}" 불러오기 완료!`);
        });

        container.appendChild(item);
    });
}

// Delete Playlist
function deletePlaylist(name) {
    if (!confirm(`"${name}" 플레이리스트를 삭제하시겠습니까?`)) return;

    const playlists = JSON.parse(localStorage.getItem('playlists') || '{}');
    delete playlists[name];
    localStorage.setItem('playlists', JSON.stringify(playlists));

    showNotification(`✅ "${name}" 삭제 완료!`);
    loadSavedPlaylists();
}

// Export Playlist as CSV
function exportPlaylist() {
    if (tracks.length === 0) {
        showNotification('❌ 내보낼 플레이리스트가 없습니다.', 'error');
        return;
    }

    const csv = 'english,korean\n' + 
        tracks.map(t => `"${t.english}","${t.korean}"`).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `playlist_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showNotification('✅ CSV 파일로 내보내기 완료!');
}

// Show Notification
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#c60055' : '#00bcd4'};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        font-family: 'Outfit', sans-serif;
        font-size: 14px;
        font-weight: 600;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        max-width: 300px;
        word-wrap: break-word;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ====================================================================
// GOOGLE CLOUD TTS INTEGRATION
// ====================================================================

// Initialize IndexedDB for audio caching
async function initAudioCache() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('EnglishPlayerTTS', 2);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            const oldVersion = event.oldVersion;
            
            if (oldVersion < 1) {
                // Create object store for version 1
                const store = db.createObjectStore('audioCache', { keyPath: 'cacheKey' });
                store.createIndex('createdAt', 'createdAt');
                store.createIndex('size', 'size');
            }
            
            if (oldVersion < 2) {
                // Upgrade to version 2: add lastAccessed index
                const store = event.target.transaction.objectStore('audioCache');
                if (!store.indexNames.contains('lastAccessed')) {
                    store.createIndex('lastAccessed', 'lastAccessed');
                }
            }
        };

        request.onsuccess = () => {
            audioCache = request.result;
            // Clean up expired cache on initialization
            cleanupExpiredCache();
            resolve(audioCache);
        };

        request.onerror = () => reject(request.error);
    });
}

// Update cache duration with actual audio duration
async function updateCacheDuration(cacheKey, actualDuration) {
    if (!audioCache) return;

    return new Promise((resolve) => {
        const tx = audioCache.transaction('audioCache', 'readwrite');
        const store = tx.objectStore('audioCache');
        const request = store.get(cacheKey);

        request.onsuccess = () => {
            const result = request.result;
            if (result) {
                // Update duration with actual value
                const oldDuration = result.duration;
                result.duration = actualDuration;
                store.put(result).onsuccess = () => {
                    console.log('[TTS Cache] ✅ Updated cache duration', {
                        cacheKey: cacheKey.substring(0, 16) + '...',
                        oldDuration: `${oldDuration.toFixed(2)}s`,
                        newDuration: `${actualDuration.toFixed(2)}s`
                    });
                    resolve();
                };
            } else {
                resolve();
            }
        };

        request.onerror = () => resolve();
    });
}

// Get cached audio from IndexedDB
async function getCachedAudio(cacheKey) {
    if (!audioCache) {
        console.warn('[TTS Cache] IndexedDB not initialized');
        return null;
    }

    return new Promise((resolve) => {
        const tx = audioCache.transaction('audioCache', 'readwrite');
        const store = tx.objectStore('audioCache');
        const request = store.get(cacheKey);

        request.onsuccess = () => {
            const result = request.result;
            const now = Date.now();
            const cacheExpiry = 30 * 24 * 60 * 60 * 1000; // 30 days
            
            if (result && (now - result.createdAt) < cacheExpiry) {
                // Update lastAccessed time
                result.lastAccessed = now;
                store.put(result).onsuccess = () => {
                    resolve(result); // Valid cache
                };
            } else {
                // Expired or not found - delete if exists
                if (result) {
                    const age = Math.round((now - result.createdAt) / (1000 * 60 * 60 * 24));
                    console.log('[TTS Cache] 🗑️ Deleting expired cache', {
                        age: `${age} days`,
                        expired: age >= 30
                    });
                    store.delete(cacheKey);
                }
                resolve(null);
            }
        };

        request.onerror = () => {
            console.error('[TTS Cache] Error reading from cache');
            resolve(null);
        };
    });
}

// Maximum cache size: 100MB
const MAX_CACHE_SIZE = 100 * 1024 * 1024;

// Store audio in IndexedDB cache with LRU management
async function storeAudioInCache(cacheKey, audioBlob, duration, voice, text) {
    if (!audioCache) {
        console.warn('[TTS Cache] Cannot store: IndexedDB not initialized');
        return;
    }

    const now = Date.now();
    const newItem = {
        cacheKey,
        audioBlob,
        duration,
        voice,
        text: text.substring(0, 100), // Store preview only
        createdAt: now,
        lastAccessed: now,
        size: audioBlob.size
    };

    console.log('[TTS Cache] 💾 Storing in cache', {
        size: `${(audioBlob.size / 1024).toFixed(2)} KB`,
        duration: `${duration.toFixed(2)}s`,
        voice: voice
    });

    // Check current cache size and enforce limit
    await enforceCacheSizeLimit(newItem.size);

    const tx = audioCache.transaction('audioCache', 'readwrite');
    const store = tx.objectStore('audioCache');
    
    await new Promise((resolve, reject) => {
        const request = store.put(newItem);
        request.onsuccess = () => {
            console.log('[TTS Cache] ✅ Cache stored successfully');
            resolve();
        };
        request.onerror = () => {
            console.error('[TTS Cache] ❌ Error storing cache:', request.error);
            reject(request.error);
        };
    });
}

// Enforce cache size limit using LRU policy
async function enforceCacheSizeLimit(newItemSize) {
    if (!audioCache) return;

    return new Promise((resolve) => {
        const tx = audioCache.transaction('audioCache', 'readwrite');
        const store = tx.objectStore('audioCache');
        const sizeIndex = store.index('size');
        const lastAccessedIndex = store.index('lastAccessed');
        
        // Calculate current total size
        let totalSize = 0;
        const items = [];
        
        const cursorRequest = store.openCursor();
        cursorRequest.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                totalSize += cursor.value.size || 0;
                items.push(cursor.value);
                cursor.continue();
            } else {
                // Check if we need to delete items
                const targetSize = totalSize + newItemSize;
                const currentSizeMB = (totalSize / 1024 / 1024).toFixed(2);
                const maxSizeMB = (MAX_CACHE_SIZE / 1024 / 1024).toFixed(2);
                
                console.log('[TTS Cache] 📊 Cache Size Check', {
                    current: `${currentSizeMB} MB`,
                    newItem: `${(newItemSize / 1024 / 1024).toFixed(2)} MB`,
                    target: `${(targetSize / 1024 / 1024).toFixed(2)} MB`,
                    max: `${maxSizeMB} MB`,
                    items: items.length
                });
                
                if (targetSize > MAX_CACHE_SIZE) {
                    // Sort by lastAccessed (oldest first)
                    items.sort((a, b) => {
                        const aTime = a.lastAccessed || a.createdAt || 0;
                        const bTime = b.lastAccessed || b.createdAt || 0;
                        return aTime - bTime;
                    });
                    
                    // Delete oldest items until we're under limit
                    let deletedSize = 0;
                    const itemsToDelete = [];
                    
                    for (const item of items) {
                        if (targetSize - deletedSize - item.size <= MAX_CACHE_SIZE) {
                            break;
                        }
                        deletedSize += item.size;
                        itemsToDelete.push(item.cacheKey);
                    }
                    
                    // Delete items
                    if (itemsToDelete.length > 0) {
                        console.log('[TTS Cache] 🗑️ LRU Cleanup: Deleting', {
                            count: itemsToDelete.length,
                            freedSpace: `${(deletedSize / 1024 / 1024).toFixed(2)} MB`,
                            reason: 'Cache size limit exceeded'
                        });
                        
                        let deleted = 0;
                        itemsToDelete.forEach(key => {
                            const deleteRequest = store.delete(key);
                            deleteRequest.onsuccess = () => {
                                deleted++;
                                if (deleted === itemsToDelete.length) {
                                    console.log('[TTS Cache] ✅ LRU Cleanup completed');
                                    resolve();
                                }
                            };
                            deleteRequest.onerror = () => {
                                deleted++;
                                if (deleted === itemsToDelete.length) {
                                    console.log('[TTS Cache] ✅ LRU Cleanup completed');
                                    resolve();
                                }
                            };
                        });
                    } else {
                        resolve();
                    }
                } else {
                    resolve();
                }
            }
        };
        
        cursorRequest.onerror = () => resolve();
    });
}

// Clean up expired cache entries
async function cleanupExpiredCache() {
    if (!audioCache) return;

    return new Promise((resolve) => {
        const tx = audioCache.transaction('audioCache', 'readwrite');
        const store = tx.objectStore('audioCache');
        const cacheExpiry = 30 * 24 * 60 * 60 * 1000; // 30 days
        const now = Date.now();
        
        const cursorRequest = store.openCursor();
        const keysToDelete = [];
        
        cursorRequest.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                const item = cursor.value;
                if (now - item.createdAt > cacheExpiry) {
                    keysToDelete.push(item.cacheKey);
                }
                cursor.continue();
            } else {
                // Delete expired items
                if (keysToDelete.length > 0) {
                    console.log('[TTS Cache] 🗑️ Expired Cache Cleanup: Deleting', {
                        count: keysToDelete.length,
                        reason: 'Cache entries expired (>30 days)'
                    });
                    
                    let deleted = 0;
                    keysToDelete.forEach(key => {
                        const deleteRequest = store.delete(key);
                        deleteRequest.onsuccess = () => {
                            deleted++;
                            if (deleted === keysToDelete.length) {
                                console.log('[TTS Cache] ✅ Expired cache cleanup completed');
                                resolve();
                            }
                        };
                        deleteRequest.onerror = () => {
                            deleted++;
                            if (deleted === keysToDelete.length) {
                                console.log('[TTS Cache] ✅ Expired cache cleanup completed');
                                resolve();
                            }
                        };
                    });
                } else {
                    resolve();
                }
            }
        };
        
        cursorRequest.onerror = () => resolve();
    });
}

// Generate cache key from text and voice (speed is handled by client playbackRate)
function generateCacheKey(text, voice) {
    const combined = `${text}_${voice}`;
    return simpleHash(combined);
}

// Simple hash function
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
}

// Convert base64 to Blob
function base64ToBlob(base64, mimeType = 'audio/mp3') {
    const bytes = atob(base64);
    const buffer = new ArrayBuffer(bytes.length);
    const array = new Uint8Array(buffer);
    for (let i = 0; i < bytes.length; i++) {
        array[i] = bytes.charCodeAt(i);
    }
    return new Blob([buffer], {type: mimeType});
}

// Format seconds to MM:SS
function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Format seconds to SS.SSs for playlist display
function formatDurationForPlaylist(seconds) {
    if (!isFinite(seconds) || seconds < 0) return '00.00s';
    return `${seconds.toFixed(2)}s`;
}

// Show loading state
function showLoadingState() {
    isLoadingAudio = true;
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'flex';
    const playBtn = document.getElementById('playBtn');
    if (playBtn) {
        playBtn.disabled = true;
        playBtn.style.opacity = '0.5';
    }
}

// Hide loading state
function hideLoadingState() {
    isLoadingAudio = false;
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'none';
    const playBtn = document.getElementById('playBtn');
    if (playBtn) {
        playBtn.disabled = false;
        playBtn.style.opacity = '1';
    }
}

// Select TTS mode
function selectTTSMode() {
    if (currentTTSMode === 'webspeech') return 'webspeech';
    if (!navigator.onLine) return 'webspeech';
    return 'google';
}

// Change TTS mode
function changeTTSMode() {
    const select = document.getElementById('ttsModeSelect');
    const voiceSelect = document.getElementById('voiceSelect');
    
    if (select) {
        const previousMode = currentTTSMode;
        const selectedValue = select.value;
        
        // Prevent selecting Google mode if API key is not available
        if (selectedValue === 'google' && !hasApiKey()) {
            showNotification('❌ Google Cloud TTS를 사용하려면 API key가 필요합니다.', 'error');
            select.value = previousMode; // Revert selection
            return;
        }
        
        currentTTSMode = selectedValue;
        localStorage.setItem('ttsMode', currentTTSMode);

        if (currentTTSMode === 'google') {
            // Enable voice selection and load Google Cloud voices
            if (voiceSelect) {
                voiceSelect.disabled = false;
                // Load voices asynchronously
                loadVoices().catch(error => {
                    console.error('Error loading voices:', error);
                    showNotification('⚠️ Failed to load voices.', 'warning');
                });
            }
            showNotification('✅ Switched to Google Cloud TTS');
        } else if (currentTTSMode === 'webspeech') {
            // Enable voice selection and load Browser TTS voices
            if (voiceSelect) {
                voiceSelect.disabled = false;
                loadBrowserVoices();
            }
            showNotification('✅ Switched to Browser TTS');
        } else {
            // Auto mode - disable voice selection
            if (voiceSelect) {
                voiceSelect.disabled = true;
                voiceSelect.value = '';
                selectedVoice = null;
                // Ensure Auto option exists
                if (voiceSelect.options.length === 0) {
                    const autoOption = document.createElement('option');
                    autoOption.value = '';
                    autoOption.textContent = 'Auto (Best English)';
                    voiceSelect.appendChild(autoOption);
                }
            }
            showNotification('✅ Auto mode enabled');
        }
    }
}

// Load TTS mode preference
function loadTTSMode() {
    const saved = localStorage.getItem('ttsMode');
    if (saved) {
        currentTTSMode = saved;
        const select = document.getElementById('ttsModeSelect');
        const voiceSelect = document.getElementById('voiceSelect');
        
        // If Google mode is selected but no API key, switch to auto
        if (currentTTSMode === 'google' && !hasApiKey()) {
            currentTTSMode = 'auto';
            localStorage.setItem('ttsMode', 'auto');
            if (select) {
                select.value = 'auto';
            }
        }
        
        if (select) {
            select.value = currentTTSMode;
        }
        
        // Apply the mode settings (enable/disable voice selection)
        if (currentTTSMode === 'google') {
            if (voiceSelect) {
                voiceSelect.disabled = false;
                // Load voices asynchronously only if API key is available
                if (hasApiKey()) {
                    loadVoices().catch(error => {
                        console.error('Error loading voices:', error);
                    });
                }
            }
        } else if (currentTTSMode === 'webspeech') {
            if (voiceSelect) {
                voiceSelect.disabled = false;
                loadBrowserVoices();
            }
        } else {
            if (voiceSelect) {
                voiceSelect.disabled = true;
                voiceSelect.value = '';
                selectedVoice = null;
                // Ensure Auto option exists
                if (voiceSelect.options.length === 0) {
                    const autoOption = document.createElement('option');
                    autoOption.value = '';
                    autoOption.textContent = 'Auto (Best English)';
                    voiceSelect.appendChild(autoOption);
                }
            }
        }
    } else {
        // Default to auto mode - disable voice selection
        const voiceSelect = document.getElementById('voiceSelect');
        if (voiceSelect) {
            voiceSelect.disabled = true;
            // Ensure Auto option exists
            if (voiceSelect.options.length === 0) {
                const autoOption = document.createElement('option');
                autoOption.value = '';
                autoOption.textContent = 'Auto (Best English)';
                voiceSelect.appendChild(autoOption);
            }
        }
    }
}

// ====================================================================
// 전역 함수들을 window 객체에 명시적으로 노출 (HTML onclick 속성에서 사용)
// ====================================================================
window.showPlayerScreen = showPlayerScreen;
window.showUploadScreen = showUploadScreen;
window.parseText = parseText;
window.pasteFromClipboard = pasteFromClipboard;
window.togglePlay = togglePlay;
window.firstTrack = firstTrack;
window.prevTrack = prevTrack;
window.nextTrack = nextTrack;
window.lastTrack = lastTrack;
window.setSpeed = setSpeed;
window.setRepeat = setRepeat;
window.changeTTSMode = changeTTSMode;
window.changeVoice = changeVoice;
window.savePlaylist = savePlaylist;
window.exportPlaylist = exportPlaylist;
window.saveApiKeyFromUpload = saveApiKeyFromUpload;
window.deleteApiKeyFromUpload = deleteApiKeyFromUpload;
window.toggleApiKeyVisibilityUpload = toggleApiKeyVisibilityUpload;
window.closeApiKeyModal = closeApiKeyModal;
window.saveApiKeyFromModal = saveApiKeyFromModal;
window.toggleApiKeyVisibility = toggleApiKeyVisibility;
// loadSampleData와 toggleDebugPanel은 이미 위에서 할당됨
