// State management
const state = {
    imageUploaded: false,
    promptsGenerated: false,
    conversationStarted: false,
    generating: false
};

// DOM elements
const uploadArea = document.getElementById('upload-area');
const imageInput = document.getElementById('image-input');
const previewImage = document.getElementById('preview-image');
const uploadStatus = document.getElementById('upload-status');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const questionsRemaining = document.getElementById('questions-remaining');
const generateButton = document.getElementById('generate-button');
const resetButton = document.getElementById('reset-button');

// Step elements
const stepUpload = document.getElementById('step-upload');
const stepDescribe = document.getElementById('step-describe');
const stepPrompts = document.getElementById('step-prompts');
const stepProgress = document.getElementById('step-progress');
const stepResults = document.getElementById('step-results');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    setupChat();
    setupButtons();
});

// Upload functionality
function setupUpload() {
    uploadArea.addEventListener('click', () => imageInput.click());
    
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadImage(file);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) {
            uploadImage(file);
        }
    });
}

async function uploadImage(file) {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showStatus('Please upload a valid image file (PNG, JPG, WEBP)', 'error');
        return;
    }
    
    // Validate file size (16MB)
    if (file.size > 16 * 1024 * 1024) {
        showStatus('File size must be less than 16MB', 'error');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewImage.style.display = 'block';
        uploadArea.querySelector('.upload-prompt').style.display = 'none';
    };
    reader.readAsDataURL(file);
    
    // Upload to server
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.imageUploaded = true;
            showStatus(`✅ ${data.message}`, 'success');
            enableChat();
        } else {
            showStatus(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Upload failed: ${error.message}`, 'error');
    }
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `status-message ${type}`;
    uploadStatus.style.display = 'block';
}

// Chat functionality
function setupChat() {
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !userInput.disabled) {
            sendMessage();
        }
    });
    
    sendButton.addEventListener('click', sendMessage);
}

function enableChat() {
    userInput.disabled = false;
    sendButton.disabled = false;
    userInput.focus();
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    userInput.value = '';
    userInput.disabled = true;
    sendButton.disabled = true;
    
    try {
        let response;
        
        if (!state.conversationStarted) {
            // Start conversation
            response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            state.conversationStarted = true;
        } else {
            // Continue conversation
            response = await fetch('/api/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
        }
        
        const data = await response.json();
        
        if (data.error) {
            addMessage(`Error: ${data.error}`, 'assistant');
        } else if (data.prompts_generated) {
            // Prompts are ready!
            addMessage(`✅ Prompts generated in ${data.response_time.toFixed(2)}s`, 'assistant');
            showPrompts(data.prompts);
        } else {
            // Continue conversation
            addMessage(data.response, 'assistant', data.response_time);
            updateQuestionsRemaining(data.questions_remaining);
        }
        
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
        
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'assistant');
        userInput.disabled = false;
        sendButton.disabled = false;
    }
}

function addMessage(text, type, responseTime = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const textP = document.createElement('p');
    // Preserve line breaks and format text properly
    textP.style.whiteSpace = 'pre-wrap';
    textP.textContent = text;
    messageDiv.appendChild(textP);
    
    if (responseTime) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = `${responseTime.toFixed(2)}s`;
        messageDiv.appendChild(timeSpan);
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom after a short delay to ensure content is rendered
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 50);
    
    // Also scroll immediately for instant feedback
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateQuestionsRemaining(remaining) {
    if (remaining > 0) {
        questionsRemaining.textContent = `${remaining} questions remaining`;
        questionsRemaining.style.display = 'block';
    } else {
        questionsRemaining.style.display = 'none';
    }
}

function showPrompts(prompts) {
    state.promptsGenerated = true;
    
    // Populate prompt sections
    document.getElementById('i2i-prompt').textContent = prompts.i2i_prompt;
    document.getElementById('i2v-prompt').textContent = prompts.i2v_prompt;
    
    // Show prompts step
    stepPrompts.style.display = 'block';
    stepPrompts.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Buttons
function setupButtons() {
    generateButton.addEventListener('click', startGeneration);
    resetButton.addEventListener('click', resetSession);
}

async function startGeneration() {
    if (!state.imageUploaded || !state.promptsGenerated) {
        return;
    }
    
    state.generating = true;
    generateButton.disabled = true;
    generateButton.innerHTML = '<span class="spinner"></span> Generating...';
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show progress step
            stepProgress.style.display = 'block';
            stepProgress.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            // Start polling for status
            pollStatus();
        } else {
            alert(`Error: ${data.error}`);
            generateButton.disabled = false;
            generateButton.textContent = '✨ Generate Video';
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        generateButton.disabled = false;
        generateButton.textContent = '✨ Generate Video';
    }
}

async function pollStatus() {
    const progressLog = document.getElementById('progress-log');
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Update log
            progressLog.innerHTML = data.log.map(line => `<div>${line}</div>`).join('');
            progressLog.scrollTop = progressLog.scrollHeight;
            
            // Check status
            if (data.status === 'complete') {
                clearInterval(interval);
                showResults(data.generated_image, data.generated_video);
            } else if (data.status === 'error') {
                clearInterval(interval);
                alert(`Generation failed: ${data.error}`);
                generateButton.disabled = false;
                generateButton.textContent = '✨ Generate Video';
            }
        } catch (error) {
            console.error('Status poll error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function showResults(imagePath, videoPath) {
    // Set result media
    document.getElementById('result-image').src = imagePath;
    document.getElementById('result-video').src = videoPath;
    
    // Show results step
    stepResults.style.display = 'block';
    stepResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function resetSession() {
    try {
        await fetch('/api/reset', { method: 'POST' });
        location.reload();
    } catch (error) {
        console.error('Reset error:', error);
        location.reload();
    }
}

