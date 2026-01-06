# Windows Event Viewer AI

A Flask-based web application that analyzes Windows Event Logs using AI models. Supports both **Microsoft Foundry Local** (for offline use) and **Google Gemini API** (for cloud-based analysis).

## Features

✅ **Responsive HTML Interface** - Modern, user-friendly web app (desktop and mobile)
✅ **Dual AI Model Support** - Microsoft Foundry Local or Google Gemini API
✅ **Event Log Analysis** - Retrieve and analyze Windows Event Viewer logs
✅ **Dropdown Selectors** - Easy selection of event log types and source names
✅ **Bulk Event Retrieval** - Get all occurrences of a specific event ID
✅ **AI-Powered Analysis** - Deep diagnostics with multiple model options
✅ **JSON Data Storage** - All analysis results saved for reference
✅ **Analysis History** - View and expand previous analysis results
✅ **Real-time Event Preview** - Preview matched events before analysis
✅ **Interactive Chat** - Follow-up questions about analyzed events

## Architecture

### Backend (Python Flask)
- `app.py` - Flask server with REST API endpoints
  - `/api/log-types` - Available event log types
  - `/api/sources/<log_type>` - Source names for a log type
  - `/api/events` - Retrieve events matching criteria
  - `/api/analyze` - Analyze events with AI model
  - `/api/chat` - Interactive chat about events
  - `/api/results` - Get all saved analyses
  - `/api/results/<filename>` - Get specific analysis
  - `/api/model-status` - Check model endpoint connectivity

### Frontend (HTML/CSS/JavaScript)
- `templates/index.html` - Main HTML page with form and tabs
- `static/style.css` - Responsive styling
- `static/script.js` - Client-side logic and API calls

### Data Storage
- `data/` directory - Stores analysis results as JSON files

## Installation

### Prerequisites
- Windows operating system (for Event Log access)
- Python 3.8+

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Choose your AI model provider:**

   **Option A: Microsoft Foundry Local (Recommended for offline use)**
   
   Prerequisites:
   - Download Microsoft Foundry Local from https://learn.microsoft.com/en-us/azure/ai-foundry/
   - Install it following official documentation
   - **Important:** Download at least one model before running the app
   
   Setup steps:
   - Launch Microsoft Foundry Local
   - It should start on `http://localhost:5272`
   - Verify it's running: `curl http://localhost:5272/openai/models`
   - Available models: Phi-4, Llama, and others
   - Example model download: `Phi-4-mini-instruct-generic-cpu`
   - Ensure model is loaded before analyzing events

   **Option B: Google Gemini API (Recommended for cloud use)**
   - Get API key from https://ai.google.dev
   - Set environment variable: `set GEMINI_API_KEY=your-api-key`
   - Or enter API key directly in the web form

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Verify setup (before first use):**
   
   If using Foundry Local:
   - Check Foundry Local is running: `curl http://localhost:5272/openai/models`
   - Should return list of available models
   - If empty, download a model in Foundry Local (e.g., Phi-4-mini-instruct-generic-cpu)
   
   If using Gemini:
   - Test API key in web form before analyzing
   - Use "Check Model Status" button to verify connectivity

5. **Access the web app:**
   - Open browser to `http://localhost:5000`

## Usage

### Basic Workflow

1. **Select Model Provider**
   - Choose "Foundry Local" for offline analysis
   - Or "Google Gemini AI" for cloud-based analysis
   - Optionally customize endpoint/model name

2. **Select Log Type** (required)
   - System, Application, Security, or Setup
   - Source list auto-populates

3. **Optional Filters**
   - **Source Name** - Filter by event source (e.g., NVIDIA, Windows Update)
   - **Event ID** - Filter by specific event ID (e.g., 41 for power events)
   - **Max Events** - Set how many events to retrieve (default: 50)

4. **Preview Events**
   - Click "Preview Events" to see matching events in a table
   - Review before sending to AI

5. **Analyze with AI**
   - Click "Analyze with AI" to send events to selected model
   - Optional: Add custom analysis prompt
   - Wait for AI analysis results

6. **Follow-up Chat** (Optional)
   - Use the chat button to ask follow-up questions
   - Context-aware responses about analyzed events

7. **View Results**
   - See AI analysis with summary, issues, causes, and recommendations
   - Results automatically saved as JSON

8. **Check History**
   - Switch to "Analysis History" tab
   - View all previous analyses
   - Click items to expand and see full details

## Configuration

### Default Settings
- **Foundry Endpoint:** `http://localhost:5272/v1/chat/completions`
- **Foundry Model:** `Phi-4-mini-instruct-generic-cpu`
- **Gemini Model:** `models/gemini-2.0-flash`
- **Default Log Type:** System
- **Max Events:** 50
- **Model Timeout:** 120 seconds

### Customization

Edit in the web form:
- Switch between Foundry Local and Gemini AI
- Change model endpoint and name
- Adjust max events retrieved
- Provide custom analysis prompts

## Event Log Types

| Type | Description |
|------|-------------|
| System | Windows kernel, drivers, hardware events |
| Application | Application errors, warnings, info |
| Security | Security events (audit logs, logins) |
| Setup | Application installation events |

## API Examples

### Get Available Log Types
```bash
curl http://localhost:5000/api/log-types
```

### Get Sources for a Log Type
```bash
curl http://localhost:5000/api/sources/System
```

### Retrieve Events
```bash
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "System",
    "source_name": "NVIDIA",
    "event_id": "41",
    "max_count": 100
  }'
```

### Analyze Events with Foundry Local
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "System",
    "source_name": "NVIDIA",
    "event_id": "41",
    "model_provider": "foundry",
    "model_endpoint": "http://localhost:5272/v1/chat/completions",
    "model_name": "Phi-4-mini-instruct-generic-cpu"
  }'
```

### Analyze Events with Gemini
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "System",
    "source_name": "NVIDIA",
    "event_id": "41",
    "model_provider": "gemini",
    "gemini_api_key": "your-api-key"
  }'
```

### Check Model Status
```bash
curl -X POST http://localhost:5000/api/model-status \
  -H "Content-Type: application/json" \
  -d '{
    "model_endpoint": "http://localhost:5272/v1/chat/completions",
    "model_name": "Phi-4-mini-instruct-generic-cpu"
  }'
```

## JSON Data Format

### Analysis Result File Structure
```json
{
  "timestamp": "2026-01-06T12:34:56.123456",
  "log_type": "System",
  "source_name": "NVIDIA",
  "event_id": "41",
  "event_count": 5,
  "events": [
    {
      "EventID": 41,
      "SourceName": "NVIDIA",
      "TimeGenerated": "2026-01-06 12:34:56",
      "EventCategory": 0,
      "EventType": 1,
      "Message": "The system has rebooted...",
      "LogType": "System"
    }
  ],
  "analysis": "AI analysis results here..."
}
```

## Fallback Analysis

If the AI model endpoint is unavailable, the app provides basic heuristic analysis:
- Detects power-related events (EventID 41, 105, Kernel-Power source)
- Provides quick recommendations without AI
- Useful for offline diagnostics

## Responsive Design

The app is fully responsive and works on:
- ✓ Desktop browsers (Chrome, Firefox, Edge, Safari)
- ✓ Tablets and mobile devices
- ✓ Small screens (480px+)

## Model Comparison

### Microsoft Foundry Local
**Advantages:**
- ✅ Completely offline (no internet required)
- ✅ Fast response (local execution)
- ✅ No API keys needed
- ✅ Free to use
- ✅ Works with various open-source models

**Requirements:**
- Foundry Local software installed and running
- Sufficient local system resources (RAM, CPU)

### Google Gemini API
**Advantages:**
- ✅ Powerful cloud models (Gemini 2.0 Flash)
- ✅ No local setup required
- ✅ Better reasoning for complex scenarios
- ✅ Always available (no maintenance needed)

**Requirements:**
- Internet connection
- Google Gemini API key
- API usage may incur costs

## Troubleshooting

### 404 Not Found / Connection Refused
- Ensure Flask is running on `http://localhost:5000`
- Check Python console for errors
- Verify no firewall blocking port 5000

### Foundry Local Model Endpoint Error
- Verify Foundry Local is running on `http://localhost:5272`
- Check model name matches available models: `curl http://localhost:5272/openai/models`
- Ensure system has enough resources (RAM, CPU)

### Gemini API Error
- Verify API key is valid and set correctly
- Check Google Gemini has API access enabled
- Verify internet connection
- Check for API rate limits or quota issues

### No Events Found
- Verify log type and filters are correct
- Some logs may not have matching events
- Try without filters (leave event ID blank)
- Ensure running with sufficient privileges for Security logs

### Port Already in Use
- Change port in app.py: `app.run(..., port=5001)`
- Or kill process on port 5000: `netstat -ano | findstr :5000`

## Files Structure
```
DemoEventViewerLogAI/
├── app.py                      # Flask backend
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Main HTML page
├── static/
│   ├── style.css              # CSS styling
│   └── script.js              # JavaScript logic
├── data/                       # JSON analysis results
└── README.md                   # This file
```

## Advanced Features

### Custom Analysis Prompts
Provide domain-specific analysis instructions:
```
"Analyze these GPU driver events and identify stability issues..."
"Look for security audit failures and explain the access violation..."
"Examine performance-related events and suggest optimizations..."
```

### Bulk Analysis
Analyze all occurrences of an event ID across different sources:
1. Select log type
2. Leave source name empty
3. Enter specific event ID
4. Retrieve and analyze all matches

### Interactive Chat
Use the chat feature to:
- Ask follow-up questions about analyzed events
- Get clarification on specific recommendations
- Explore alternative solutions
- Context-aware diagnostics

## Performance Tips

- **Max Events:** Start with 50, increase if needed (max 500)
- **Event ID Filter:** Dramatically speeds up retrieval
- **Source Filter:** Use when analyzing specific components
- **Prompt Length:** Longer custom prompts may take longer
- **Model Choice:** Foundry Local is faster; Gemini is more accurate

## Requirements

- Windows OS (Event Log access)
- Python 3.8+
- Flask, requests, pywin32, google-generativeai packages
- Either:
  - Microsoft Foundry Local installed locally with at least one model downloaded, OR
  - Internet connection + Google Gemini API key
- 4GB+ RAM recommended
- ~2GB disk space for models (Foundry only)

## Security Notes

- Store API keys in environment variables, not in code
- GEMINI_API_KEY env var is read automatically
- Web form accepts keys for temporary use
- Analysis results are stored locally in `data/` directory
- No data is sent outside your network with Foundry Local

## License

This project uses:
- Windows Event Log APIs (Microsoft)
- Microsoft Foundry Local API
- Google Generative AI API

## Support

For issues with:
- **Flask/Python:** Check Python version and installed packages
- **Event Logs:** Ensure running as Administrator if needed for Security logs
- **Foundry Local:** Visit https://learn.microsoft.com/en-us/azure/ai-foundry/
- **Gemini API:** Visit https://ai.google.dev/
- **This Project:** Check this README or review error messages

## Version History

**v2.0** (Current) - January 2026
- ✨ Added Microsoft Foundry Local integration
- ✨ Dual model provider support
- 🔧 Refactored code structure
- 📚 Improved documentation

**v1.0** - Gemini-only version

---

**Last Updated:** January 6, 2026
**Maintainer:** Windows Event Viewer AI Project
