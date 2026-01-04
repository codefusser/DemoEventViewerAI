# Windows Event Viewer AI Analysis App

A responsive web application that analyzes Windows Event Logs using Microsoft Foundry Local AI models.

## Features

✅ **Responsive HTML Interface** - Modern, user-friendly web app that works on desktop and mobile
✅ **Event Log Analysis** - Retrieve and analyze Windows Event Viewer logs
✅ **Dropdown Selectors** - Easy selection of event log types and source names
✅ **Bulk Event Retrieval** - Get all occurrences of a specific event ID for comprehensive analysis
✅ **AI-Powered Analysis** - Uses Microsoft Foundry Local API for local, offline analysis
✅ **JSON Data Storage** - All analysis results saved as JSON for future reference
✅ **Analysis History** - View and expand previous analysis results
✅ **Real-time Event Preview** - Preview matched events in a formatted table before analysis

## Architecture

### Backend (Python Flask)
- `app.py` - Flask server with REST API endpoints
  - `/api/log-types` - Get available event log types
  - `/api/sources/<log_type>` - Get source names for a log type
  - `/api/events` - Retrieve events matching criteria
  - `/api/analyze` - Analyze events with AI model
  - `/api/results` - Get all saved analyses
  - `/api/results/<filename>` - Get specific analysis

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
- Microsoft Foundry Local running on `http://localhost:5272`

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install flask requests pywin32
   ```

2. **Configure Microsoft Foundry Local:**
   - Ensure Foundry Local is running on `http://localhost:5272`
   - List available models: `curl http://localhost:5272/openai/models`
   - Download a model if needed

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the web app:**
   - Open browser to `http://localhost:5000`

## Usage

### Basic Workflow

1. **Select Log Type** (required)
   - Choose from: System, Application, Security, Setup
   - Source list auto-populates

2. **Optional Filters**
   - **Source Name** - Filter by event source (e.g., NVIDIA, Windows Update)
   - **Event ID** - Filter by specific event ID (e.g., 41 for power events)
   - **Max Events** - Set how many events to retrieve (default: 50)

3. **Preview Events**
   - Click "Preview Events" to see matching events in a table
   - Review before sending to AI

4. **Analyze with AI**
   - Click "Analyze with AI" to send events to Foundry Local
   - Optional: Add custom analysis prompt
   - Wait for AI analysis results

5. **View Results**
   - See AI analysis with summary, issues, causes, and recommendations
   - Results automatically saved as JSON

6. **Check History**
   - Switch to "Analysis History" tab
   - View all previous analyses
   - Click items to expand and see full details

## Configuration

### Default Settings
- **Model Endpoint:** `http://localhost:5272/v1/chat/completions`
- **Model Name:** `Phi-4-mini-instruct-generic-cpu`
- **Default Log Type:** System
- **Max Events:** 50

### Customization

Edit in the web form:
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

### Analyze Events
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "System",
    "source_name": "NVIDIA",
    "event_id": "41",
    "model_endpoint": "http://localhost:5272/v1/chat/completions",
    "model_name": "Phi-4-mini-instruct-generic-cpu"
  }'
```

## JSON Data Format

### Analysis Result File Structure
```json
{
  "timestamp": "2026-01-03T22:38:45.123456",
  "log_type": "System",
  "source_name": "NVIDIA",
  "event_id": "41",
  "event_count": 5,
  "events": [
    {
      "EventID": 41,
      "SourceName": "NVIDIA",
      "TimeGenerated": "2026-01-03 22:38:45",
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

## Responsive Design

The app is fully responsive and works on:
- ✓ Desktop browsers (Chrome, Firefox, Edge, Safari)
- ✓ Tablets and mobile devices
- ✓ Small screens (480px+)

## Troubleshooting

### 404 Not Found
- Ensure Flask is running on `http://localhost:5000`
- Check Python console for errors

### Model endpoint error
- Verify Foundry Local is running on `http://localhost:5272`
- Check model name matches available models: `curl http://localhost:5272/openai/models`

### No events found
- Verify log type and filters are correct
- Some logs may not have matching events
- Try without filters (leave event ID blank)

### Port already in use
- Change port in app.py: `app.run(..., port=5001)`
- Or kill process on port 5000

## Files Structure
```
DemoEventViewerLogAI/
├── app.py                 # Flask backend
├── templates/
│   └── index.html        # Main HTML page
├── static/
│   ├── style.css        # CSS styling
│   └── script.js        # JavaScript logic
├── data/                 # JSON analysis results
└── README.md            # This file
```

## Advanced Features

### Custom Analysis Prompts
Provide domain-specific analysis instructions:
```
"Analyze these GPU driver events and identify stability issues..."
"Look for security audit failures and explain the access violation..."
```

### Bulk Analysis
Analyze all occurrences of an event ID across different sources:
1. Select log type
2. Leave source name empty
3. Enter specific event ID
4. Retrieve and analyze all matches

## Performance Tips

- **Max Events:** Start with 50, increase if needed (max 500)
- **Event ID Filter:** Dramatically speeds up retrieval
- **Source Filter:** Use when analyzing specific components
- **Prompt Length:** Longer custom prompts may take longer to analyze

## Requirements

- Windows OS (Event Log access)
- Python 3.8+
- Flask, requests, pywin32 packages
- Microsoft Foundry Local API running locally
- 4GB+ RAM recommended
- ~2GB disk space for models (depends on model size)

## License

This project uses Windows Event Log APIs and Microsoft Foundry Local API.

## Support

For issues with:
- **Flask/Python:** Check Python version and installed packages
- **Event Logs:** Ensure running as Administrator if needed
- **Foundry Local:** Visit https://learn.microsoft.com/en-us/azure/ai-foundry/

---

**Last Updated:** January 3, 2026
