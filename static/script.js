// App State
const appState = {
    logTypes: [],
    sources: [],
    currentLogType: null,
};

// DOM Elements
const logTypeSelect = document.getElementById('logType');
const sourceNameSelect = document.getElementById('sourceName');
const eventIdInput = document.getElementById('eventId');
const maxCountInput = document.getElementById('maxCount');
const customPromptInput = document.getElementById('customPrompt');
const analyzerForm = document.getElementById('analyzerForm');
const previewBtn = document.getElementById('previewBtn');

const eventsPreview = document.getElementById('eventsPreview');
const previewLoading = document.getElementById('previewLoading');
const eventsTable = document.getElementById('eventsTable');
const previewError = document.getElementById('previewError');

const analysisResults = document.getElementById('analysisResults');
const resultLoading = document.getElementById('resultLoading');
const analysisContent = document.getElementById('analysisContent');
const resultError = document.getElementById('resultError');

const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

let lastRetrievedEvents = null;
// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    loadLogTypes();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    logTypeSelect.addEventListener('change', handleLogTypeChange);
    analyzerForm.addEventListener('submit', handleFormSubmit);
    previewBtn.addEventListener('click', handlePreview);
    
    // Add model provider change listener
    const modelProviderSelect = document.getElementById('modelProvider');
    if (modelProviderSelect) {
        modelProviderSelect.addEventListener('change', handleModelProviderChange);
    }
    
    // Add model status check
    const checkModelBtn = document.getElementById('checkModelBtn');
    if (checkModelBtn) {
        checkModelBtn.addEventListener('click', checkModelStatus);
    }
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => handleTabChange(e.target.dataset.tab, e.target));
    });
}

// Handle Model Provider Change
function handleModelProviderChange() {
    const provider = document.getElementById('modelProvider').value;
    const foundrySection = document.getElementById('foundrySection');
    const geminiSection = document.getElementById('geminiSection');
    
    if (provider === 'gemini') {
        foundrySection.style.display = 'none';
        geminiSection.style.display = 'flex';
    } else {
        foundrySection.style.display = 'flex';
        geminiSection.style.display = 'none';
    }
}

// Load Log Types
function loadLogTypes() {
    fetch('/api/log-types')
        .then(response => response.json())
        .then(data => {
            appState.logTypes = data.log_types;
            populateLogTypes();
        })
        .catch(error => {
            console.error('Error loading log types:', error);
            showError(previewError, 'Failed to load log types');
        });
}

// Populate Log Types Dropdown
function populateLogTypes() {
    logTypeSelect.innerHTML = '<option value="">-- Select Log Type --</option>';
    appState.logTypes.forEach(logType => {
        const option = document.createElement('option');
        option.value = logType;
        option.textContent = logType;
        logTypeSelect.appendChild(option);
    });
}

// Handle Log Type Change
function handleLogTypeChange() {
    const logType = logTypeSelect.value;
    appState.currentLogType = logType;
    
    if (!logType) {
        sourceNameSelect.innerHTML = '<option value="">-- Any Source --</option>';
        appState.sources = [];
        return;
    }
    
    // Show loading state
    sourceNameSelect.innerHTML = '<option value="">-- Loading sources... --</option>';
    sourceNameSelect.disabled = true;
    
    // Load sources for selected log type
    fetch(`/api/sources/${encodeURIComponent(logType)}`)
        .then(response => response.json())
        .then(data => {
            appState.sources = data.sources;
            populateSources();
            sourceNameSelect.disabled = false;
        })
        .catch(error => {
            console.error('Error loading sources:', error);
            sourceNameSelect.innerHTML = '<option value="">Error loading sources</option>';
            sourceNameSelect.disabled = false;
        });
}

// Populate Sources Dropdown
function populateSources() {
    sourceNameSelect.innerHTML = '<option value="">-- Any Source --</option>';
    appState.sources.forEach(source => {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = source;
        sourceNameSelect.appendChild(option);
    });
}

// Handle Preview Button
function handlePreview() {
    const logType = logTypeSelect.value;
    
    if (!logType) {
        showError(previewError, 'Please select a log type');
        return;
    }
    
    loadAndDisplayEvents();
}

// Load and Display Events
function loadAndDisplayEvents() {
    const logType = logTypeSelect.value;
    const sourceName = sourceNameSelect.value || null;
    const eventId = eventIdInput.value || null;
    const maxCount = maxCountInput.value || 50;
    
    eventsPreview.style.display = 'block';
    previewLoading.style.display = 'block';
    eventsTable.style.display = 'none';
    previewError.style.display = 'none';
    
    const payload = {
        log_type: logType,
        source_name: sourceName,
        event_id: eventId,
        max_count: parseInt(maxCount)
    };
    
    fetch('/api/events', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            previewLoading.style.display = 'none';

            if (data.error) {
                showError(previewError, data.error);
                return;
            }

            if (!data.events || data.events.length === 0) {
                showError(previewError, 'No events found matching the criteria');
                return;
            }

            // store retrieved events for chat context
            lastRetrievedEvents = data.events;

            populateEventsTable(data.events);
            eventsTable.style.display = 'table';
        })
        .catch(error => {
            console.error('Error loading events:', error);
            previewLoading.style.display = 'none';
            showError(previewError, 'Failed to load events: ' + error.message);
        });
    
}

// Populate Events Table
function populateEventsTable(events) {
    const tbody = eventsTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    events.forEach(event => {
        const row = document.createElement('tr');
        const message = event.Message ? (event.Message.length > 100 ? event.Message.substring(0, 100) + '...' : event.Message) : 'N/A';
        
        row.innerHTML = `
            <td>${event.TimeGenerated}</td>
            <td>${event.EventID}</td>
            <td>${event.SourceName}</td>
            <td>${event.EventType}</td>
            <td title="${event.Message}">${message}</td>
        `;
        tbody.appendChild(row);
    });
}

// Handle Form Submit
function handleFormSubmit(e) {
    e.preventDefault();
    
    const logType = logTypeSelect.value;
    
    if (!logType) {
        showError(resultError, 'Please select a log type');
        analysisResults.style.display = 'block';
        analysisContent.style.display = 'none';
        return;
    }
    
    analyzeEvents();
}

// Analyze Events
function analyzeEvents() {
    const logType = logTypeSelect.value;
    const sourceName = sourceNameSelect.value || null;
    const eventId = eventIdInput.value || null;
    const customPrompt = customPromptInput.value || null;
    const modelProvider = document.getElementById('modelProvider').value;
    const modelEndpoint = document.getElementById('modelEndpoint').value;
    const modelName = document.getElementById('modelName').value;
    const geminiApiKey = document.getElementById('geminiApiKey').value;
    
    analysisResults.style.display = 'block';
    resultLoading.style.display = 'block';
    analysisContent.style.display = 'none';
    resultError.style.display = 'none';
    
    const payload = {
        log_type: logType,
        source_name: sourceName,
        event_id: eventId,
        custom_prompt: customPrompt,
        model_provider: modelProvider,
        model_endpoint: modelEndpoint,
        model_name: modelName,
        gemini_api_key: geminiApiKey
    };
    
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            resultLoading.style.display = 'none';
            
            if (data.error) {
                showError(resultError, data.error);
                return;
            }
            // store events so chat can use them as context
            if (data.events && Array.isArray(data.events) && data.events.length > 0) {
                lastRetrievedEvents = data.events;
            }

            displayAnalysisResults(data);
            analysisContent.style.display = 'block';
            loadAnalysisHistory(); // Refresh history
        })
        .catch(error => {
            console.error('Error analyzing events:', error);
            resultLoading.style.display = 'none';
            showError(resultError, 'Failed to analyze events: ' + error.message);
        });
}

// Display Analysis Results
function displayAnalysisResults(data) {
    document.getElementById('resultLogType').textContent = data.events[0]?.LogType || 'N/A';
    document.getElementById('resultSourceName').textContent = data.events[0]?.SourceName || 'Any';
    document.getElementById('resultEventId').textContent = eventIdInput.value || 'Any';
    document.getElementById('resultEventCount').textContent = data.events.length;
    document.getElementById('resultFile').textContent = data.result_file.split('\\').pop() || data.result_file;
    document.getElementById('analysisText').textContent = data.analysis;
}

// Show Error
function showError(container, message) {
    container.textContent = message;
    container.style.display = 'block';
}

// Handle Tab Change
function handleTabChange(tabName, btnElement) {
    // Hide all tabs
    tabContents.forEach(content => content.classList.remove('active'));

    // Deactivate all buttons
    tabButtons.forEach(btn => btn.classList.remove('active'));

    // Show selected tab
    const tab = document.getElementById(tabName);
    if (tab) tab.classList.add('active');
    if (btnElement) btnElement.classList.add('active');

    // Load history if switching to history tab
    if (tabName === 'history') {
        loadAnalysisHistory();
    }
}

// Load Analysis History
function loadAnalysisHistory() {
    const historyLoading = document.getElementById('historyLoading');
    const historyList = document.getElementById('historyList');
    
    historyLoading.style.display = 'block';
    historyList.innerHTML = '';
    
    fetch('/api/results')
        .then(response => response.json())
        .then(data => {
            historyLoading.style.display = 'none';
            
            if (!data.results || data.results.length === 0) {
                historyList.innerHTML = '<p style="text-align: center; color: #666;">No analysis history yet</p>';
                return;
            }
            
            data.results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'history-item';
                
                const timestamp = new Date(result.timestamp).toLocaleString();
                const sourceText = result.source_name || 'Any Source';
                const eventIdText = result.event_id || 'Any Event';
                
                item.innerHTML = `
                    <div class="history-item-header">
                        <div>
                            <h3>${result.log_type}</h3>
                            <div class="history-item-meta">${timestamp}</div>
                        </div>
                    </div>
                    <div class="history-item-details">
                        <p><strong>Source:</strong> ${sourceText}</p>
                        <p><strong>Event ID:</strong> ${eventIdText}</p>
                        <p><strong>Events:</strong> ${result.event_count}</p>
                        <p style="margin-top: 10px; max-height: 100px; overflow: hidden; color: #555;">
                            ${result.analysis.substring(0, 150)}...
                        </p>
                    </div>
                `;
                
                item.addEventListener('click', () => expandHistoryItem(result));
                historyList.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error loading history:', error);
            historyLoading.style.display = 'none';
            historyList.innerHTML = '<p style="color: #e74c3c;">Failed to load analysis history</p>';
        });
}

// Expand History Item
function expandHistoryItem(result) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 8px; max-width: 700px; max-height: 80vh; overflow-y: auto; position: relative;">
            <button onclick="this.parentElement.parentElement.remove()" style="position: absolute; top: 10px; right: 10px; border: none; font-size: 24px; background: none; cursor: pointer;">&times;</button>
            <h2>${result.log_type} - ${new Date(result.timestamp).toLocaleString()}</h2>
            <div style="margin: 20px 0;">
                <p><strong>Source:</strong> ${result.source_name || 'Any Source'}</p>
                <p><strong>Event ID:</strong> ${result.event_id || 'Any Event'}</p>
                <p><strong>Events Found:</strong> ${result.event_count}</p>
                <p><strong>File:</strong> ${result.filename}</p>
            </div>
            <h3>AI Analysis</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto;">${result.analysis}</pre>
        </div>
    `;
    
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;';
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Check Model Status
function checkModelStatus() {
    const modelEndpoint = document.getElementById('modelEndpoint').value;
    const modelName = document.getElementById('modelName').value;
    const statusBtn = document.getElementById('checkModelBtn');
    const statusMessage = document.getElementById('modelStatusMessage');
    
    if (!statusMessage) {
        console.error('Status message element not found');
        return;
    }
    
    // Show loading state
    statusBtn.disabled = true;
    statusBtn.textContent = 'Checking...';
    statusMessage.style.display = 'block';
    statusMessage.className = 'info-message';
    statusMessage.textContent = 'Checking model status...';
    
    const payload = {
        model_endpoint: modelEndpoint,
        model_name: modelName
    };
    
    fetch('/api/model-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            statusBtn.disabled = false;
            statusBtn.textContent = 'Check Model Status';
            
            if (data.status === 'ok') {
                statusMessage.className = 'success-message';
                statusMessage.textContent = `✓ Model is responding: ${data.message}`;
            } else {
                statusMessage.className = 'error-message';
                statusMessage.textContent = `✗ ${data.status.toUpperCase()}: ${data.message}\\nDetails: ${data.details}`;
            }
        })
        .catch(error => {
            console.error('Error checking model status:', error);
            statusBtn.disabled = false;
            statusBtn.textContent = 'Check Model Status';
            statusMessage.className = 'error-message';
            statusMessage.textContent = 'Error checking model status: ' + error.message;
        });
}

// Chat UI logic
        document.addEventListener('DOMContentLoaded', () => {
          const chatBtn = document.getElementById('chatBtn');
          const chatModal = document.getElementById('chatModal');
          const chatClose = document.getElementById('chatClose');
          const chatSend = document.getElementById('chatSend');
          const chatInput = document.getElementById('chatInput');
          const chatMessages = document.getElementById('chatMessages');
          const chatContextInfo = document.getElementById('chatContextInfo');
        
          if (chatBtn) chatBtn.addEventListener('click', openChat);
          if (chatClose) chatClose.addEventListener('click', closeChat);
          if (chatSend) chatSend.addEventListener('click', sendChatMessage);
          if (chatInput) chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendChatMessage();
          });
        
          function openChat() {
            if (!chatModal) return;
            chatModal.style.display = 'flex';
            chatMessages.innerHTML = '';
            if (lastRetrievedEvents && lastRetrievedEvents.length > 0) {
              chatContextInfo.textContent = `${lastRetrievedEvents.length} events loaded for context.`;
              appendSystemNote('Events loaded — ask follow-up questions about these events.');
            } else {
              chatContextInfo.textContent = 'No events loaded yet. Preview or analyze events first.';
            }
            chatInput.focus();
          }
        
          function closeChat() {
            if (!chatModal) return;
            chatModal.style.display = 'none';
          }
        
          function appendSystemNote(text) {
            const el = document.createElement('div');
            el.className = 'chat-message assistant';
            el.textContent = text;
            chatMessages.appendChild(el);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        
          function appendMessage(role, text) {
            const el = document.createElement('div');
            el.className = 'chat-message ' + (role === 'user' ? 'user' : 'assistant');
            el.textContent = text;
            chatMessages.appendChild(el);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        
          function sendChatMessage() {
            const question = chatInput.value && chatInput.value.trim();
            if (!question) return;
            appendMessage('user', question);
            chatInput.value = '';
            // Build payload
            const modelProvider = document.getElementById('modelProvider').value;
            const payload = {
              model_provider: modelProvider,
              model_endpoint: document.getElementById('modelEndpoint').value,
              model_name: document.getElementById('modelName').value,
              gemini_api_key: document.getElementById('geminiApiKey').value,
              events: lastRetrievedEvents,
              question: question
            };
        
            appendMessage('assistant', 'Thinking...');
            // POST to backend chat endpoint
            fetch('/api/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
              // remove temporary "Thinking..." message
              const last = chatMessages.lastElementChild;
              if (last && last.textContent === 'Thinking...') last.remove();
        
              if (data.error) {
                appendMessage('assistant', 'Error: ' + data.error);
                return;
              }
              appendMessage('assistant', data.reply || 'No reply from model.');
            })
            .catch(err => {
              const last = chatMessages.lastElementChild;
              if (last && last.textContent === 'Thinking...') last.remove();
              appendMessage('assistant', 'Chat error: ' + (err.message || err));
            });
          }
        });
