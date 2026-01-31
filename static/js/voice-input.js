// Configuration
const config = {
    theme: 'dark',
    lang: 'ko-KR',
    apiBase: '',
    token: '',
    sampleRate: 16000
};

// Parse URL parameters
const urlParams = new URLSearchParams(window.location.search);
config.theme = urlParams.get('theme') || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
config.lang = urlParams.get('lang') || 'ko-KR';
config.apiBase = urlParams.get('api_base') || window.location.origin;
config.token = urlParams.get('token') || '';

// Apply theme
document.documentElement.setAttribute('data-theme', config.theme);

// DOM Elements
const overlay = document.getElementById('overlay');
const popup = document.getElementById('popup');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const visualizer = document.getElementById('visualizer');
const textArea = document.getElementById('textArea');
const btnCancel = document.getElementById('btnCancel');
const btnMic = document.getElementById('btnMic');
const btnSubmit = document.getElementById('btnSubmit');
const errorMessage = document.getElementById('errorMessage');

// State
let isRecording = false;
let audioContext = null;
let mediaStream = null;
let processor = null;
let websocket = null;
let sessionId = null;

// Silence detection
const SILENCE_THRESHOLD = 0.01;  // RMS threshold for silence
const SILENCE_TIMEOUT_MS = 2000; // Auto-stop after 2 seconds of silence
let lastSoundTime = 0;
let silenceCheckInterval = null;

// Create visualizer bars
const barCount = 20;
for (let i = 0; i < barCount; i++) {
    const bar = document.createElement('div');
    bar.className = 'visualizer-bar';
    visualizer.appendChild(bar);
}

// Utility functions
function postMessage(data) {
    if (window.ReactNativeWebView) {
        window.ReactNativeWebView.postMessage(JSON.stringify(data));
    } else {
        console.log('PostMessage:', data);
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    setTimeout(() => errorMessage.classList.remove('show'), 5000);
}

function updateStatus(status, text) {
    statusDot.className = 'status-dot ' + status;
    statusText.textContent = text;
}

function setTheme(theme) {
    config.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
}

// Audio processing
function floatTo16BitPCM(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < float32Array.length; i++) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Uint8Array(buffer);
}

function resample(audioData, fromSampleRate, toSampleRate) {
    if (fromSampleRate === toSampleRate) {
        return audioData;
    }
    const ratio = fromSampleRate / toSampleRate;
    const newLength = Math.round(audioData.length / ratio);
    const result = new Float32Array(newLength);
    for (let i = 0; i < newLength; i++) {
        const index = i * ratio;
        const low = Math.floor(index);
        const high = Math.min(low + 1, audioData.length - 1);
        const frac = index - low;
        result[i] = audioData[low] * (1 - frac) + audioData[high] * frac;
    }
    return result;
}

// Calculate RMS (Root Mean Square) for silence detection
function calculateRMS(audioData) {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
        sum += audioData[i] * audioData[i];
    }
    return Math.sqrt(sum / audioData.length);
}

// Check for silence and auto-stop
function checkSilenceTimeout() {
    if (!isRecording) return;

    const now = Date.now();
    if (lastSoundTime > 0 && (now - lastSoundTime) >= SILENCE_TIMEOUT_MS) {
        console.log('Auto-stopping due to silence');
        stopRecording();
    }
}

// WebSocket connection
function connectWebSocket() {
    const wsProtocol = config.apiBase.startsWith('https') ? 'wss' : 'ws';
    const wsBase = config.apiBase.replace(/^https?/, wsProtocol);
    const tokenParam = config.token ? `&token=${encodeURIComponent(config.token)}` : '';
    const wsUrl = `${wsBase}/api/v1/voice/stream?language=${config.lang}&sample_rate=${config.sampleRate}${tokenParam}`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('recording', '음성 인식 중...');
    };

    websocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            // Handle session created notification (final result from server)
            if (data.type === 'session_created') {
                sessionId = data.session_id;
                console.log('Session created:', sessionId);

                // Display final transcript from server
                if (data.transcript) {
                    textArea.value = data.transcript;
                    btnSubmit.disabled = !data.transcript.trim();
                }

                // Now safe to close WebSocket
                if (websocket) {
                    websocket.close();
                    websocket = null;
                }
                updateStatus('', '완료되었습니다');
                return;
            }

            // Handle no speech detected
            if (data.type === 'no_speech') {
                console.log('No speech detected');

                // Close WebSocket
                if (websocket) {
                    websocket.close();
                    websocket = null;
                }
                updateStatus('', '음성이 감지되지 않았습니다');
                return;
            }

            // Handle STT result - only show final results
            if (data.text !== undefined && data.is_final) {
                textArea.value = data.text;
                btnSubmit.disabled = !data.text.trim();
            }
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
        }
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        showError('연결 오류가 발생했습니다');
        stopRecording();
    };

    websocket.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        if (isRecording) {
            updateStatus('processing', '처리 중...');
        }
    };
}

// Recording functions
async function startRecording() {
    // Clear previous text
    textArea.value = '';
    btnSubmit.disabled = true;

    try {
        // Request microphone access
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: {ideal: config.sampleRate},
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: config.sampleRate
        });

        const source = audioContext.createMediaStreamSource(mediaStream);
        const actualSampleRate = audioContext.sampleRate;

        // Use ScriptProcessorNode for audio processing
        // Note: This is deprecated but widely supported in WebViews
        const bufferSize = 4096;
        processor = audioContext.createScriptProcessor(bufferSize, 1, 1);

        // Connect WebSocket
        connectWebSocket();

        processor.onaudioprocess = (e) => {
            if (!isRecording || !websocket || websocket.readyState !== WebSocket.OPEN) {
                return;
            }

            const inputData = e.inputBuffer.getChannelData(0);

            // Check for sound (silence detection)
            const rms = calculateRMS(inputData);
            const hasSound = rms > SILENCE_THRESHOLD;

            // Toggle visualizer animation
            if (hasSound) {
                visualizer.classList.add('has-sound');
                lastSoundTime = Date.now();
            } else {
                visualizer.classList.remove('has-sound');
            }

            // Resample if necessary
            const resampled = resample(inputData, actualSampleRate, config.sampleRate);

            // Convert to 16-bit PCM
            const pcmData = floatTo16BitPCM(resampled);

            // Send to WebSocket
            websocket.send(pcmData);
        };

        source.connect(processor);
        processor.connect(audioContext.destination);

        isRecording = true;
        btnMic.classList.add('recording');
        visualizer.classList.add('active');
        updateStatus('recording', '듣고 있습니다...');

        // Initialize silence detection
        lastSoundTime = Date.now();
        silenceCheckInterval = setInterval(checkSilenceTimeout, 500);

    } catch (error) {
        console.error('Failed to start recording:', error);
        if (error.name === 'NotAllowedError') {
            showError('마이크 접근이 거부되었습니다');
            postMessage({type: 'error', message: 'microphone_permission_denied'});
        } else {
            showError('마이크를 시작할 수 없습니다');
            postMessage({type: 'error', message: error.message});
        }
    }
}

function stopRecording(closeWebSocket = false) {
    isRecording = false;
    btnMic.classList.remove('recording');
    visualizer.classList.remove('active');
    visualizer.classList.remove('has-sound');

    // Clear silence detection interval
    if (silenceCheckInterval) {
        clearInterval(silenceCheckInterval);
        silenceCheckInterval = null;
    }

    if (processor) {
        processor.disconnect();
        processor = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }

    if (websocket) {
        if (closeWebSocket) {
            // Immediately close (cancel scenario)
            websocket.close();
            websocket = null;
            updateStatus('', '마이크 버튼을 눌러 시작하세요');
        } else if (websocket.readyState === WebSocket.OPEN) {
            // Normal stop - send stop message and wait for session_created
            updateStatus('processing', '처리 중...');
            websocket.send(JSON.stringify({type: 'stop'}));
        }
    } else {
        updateStatus('', '마이크 버튼을 눌러 시작하세요');
    }
}

// Event handlers
btnMic.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

btnCancel.addEventListener('click', () => {
    stopRecording(true);
    closePopup();
    postMessage({type: 'cancel'});
});

btnSubmit.addEventListener('click', () => {
    const text = textArea.value.trim();
    if (!text) return;

    stopRecording();

    postMessage({
        type: 'submit',
        text: text,
        sessionId: sessionId
    });

    closePopup();
});

// Close when clicking overlay background
overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
        stopRecording(true);
        closePopup();
        postMessage({type: 'cancel'});
    }
});

// Prevent closing when clicking popup
popup.addEventListener('click', (e) => {
    e.stopPropagation();
});

// Public API for React Native
function openPopup() {
    overlay.classList.add('active');
    textArea.value = '';
    btnSubmit.disabled = true;
    sessionId = null;
}

function closePopup() {
    overlay.classList.remove('active');
    stopRecording(true);
}

function setText(text) {
    textArea.value = text;
    btnSubmit.disabled = !text.trim();
}

// Expose functions globally for React Native
window.openPopup = openPopup;
window.closePopup = closePopup;
window.setTheme = setTheme;
window.setText = setText;

// Auto-open popup on load (can be disabled via URL param)
if (urlParams.get('auto_open') !== 'false') {
    openPopup();
}