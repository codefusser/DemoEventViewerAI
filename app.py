"""
This is the main Flask application for the Windows Event Log AI Diagnostic Tool.
It provides endpoints to retrieve event logs, analyze them using AI models,
and serve the web interface.
"""

# Imports
import win32evtlog
import win32evtlogutil
import json
import requests
from requests import exceptions as req_ex
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from pathlib import Path
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Flask app setup
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configuration
DEFAULT_MODEL_ENDPOINT = "http://localhost:50146/v1/chat/completions"
# DEFAULT_MODEL_NAME = "qwen2.5-7b-instruct-generic-cpu:4"
DEFAULT_MODEL_NAME = "Phi-4-mini-reasoning-generic-cpu:3"
MODEL_TIMEOUT = 120  # Increased timeout for model inference (seconds)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Get from env var or form input
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Standard Windows Event Log types
EVENTLOG_TYPES = ["System", "Application", "Security", "Setup"]

# Helper Functions
# ----------------
# ------------------------------------------------------------------------------
# Windows Event Log Functions
# ------------------------------------------------------------------------------
# ----------------------------------------------------------------------
# Event Log Retrieval and Analysis
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Event Log Retrieval
# ----------------------------------------------------------------------    
# ----------------------------------------------------------------------  
def get_all_event_sources(log_type):
    """Retrieve all source names from a Windows Event Log type."""
    try:
        handle = win32evtlog.OpenEventLog(None, log_type)
        # Read events to discover sources - note: sources come from event records
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(handle, flags, 0)
        
        sources = set()
        # Read a batch of events to discover sources
        for event in events[:1000]:  # Sample first 1000 events
            if hasattr(event, 'SourceName'):
                sources.add(event.SourceName)
        
        win32evtlog.CloseEventLog(handle)
        return sorted(list(sources))
    except Exception as e:
        return [f"Error: {str(e)}"]

# ----------------------------------------------------------------------
# Event Log Retrieval by Criteria
# ----------------------------------------------------------------------
def get_events_by_criteria(log_type, source_name=None, event_id=None, max_count=100):
    """Retrieve events matching specified criteria."""
    try:
        handle = win32evtlog.OpenEventLog(None, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(handle, flags, 0)
        
        matching_events = []
        
        for event in events:
            # Filter by source name if specified
            if source_name and event.SourceName != source_name:
                continue
            
            # Filter by event ID if specified
            if event_id and event.EventID != int(event_id):
                continue
            
            # Format message safely
            try:
                message = win32evtlogutil.SafeFormatMessage(event, log_type)
            except Exception:
                message = ""
                try:
                    if hasattr(event, "StringInserts") and event.StringInserts:
                        message = " ".join([str(s) for s in event.StringInserts])
                except Exception:
                    message = ""
            
            event_data = {
                "EventID": event.EventID,
                "SourceName": event.SourceName,
                "TimeGenerated": event.TimeGenerated.Format(),
                "EventCategory": event.EventCategory,
                "EventType": event.EventType,
                "Message": message,
                "LogType": log_type
            }
            matching_events.append(event_data)
            
            if len(matching_events) >= max_count:
                break
        
        win32evtlog.CloseEventLog(handle)
        return matching_events
    except Exception as e:
        return {"error": str(e)}

# ----------------------------------------------------------------------
# AI Model Analysis Functions
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Local Fallback Analysis
# ----------------------------------------------------------------------
def local_fallback_analysis(event_data):
    """Simple heuristic analysis if model endpoint is unavailable."""
    eid = int(event_data.get("EventID", 0) or 0)
    src = str(event_data.get("SourceName", "") or "")
    msg = str(event_data.get("Message", "") or "").strip()

    parts = []
    parts.append(f"Source: {src}")
    parts.append(f"EventID: {eid}")
    if msg:
        parts.append(f"Message excerpt: {msg[:400]}")

    if "Kernel-Power" in src or eid in (41, 105):
        parts.append("Likely issue: Power-related event (unexpected shutdown, sleep/resume, or power loss).")
        parts.append("Recommended: Check power supply/UPS, AC adapter, battery; review surrounding events.")
    else:
        parts.append("No clear pattern detected from heuristics.")
        parts.append("Recommended: Review full event message and check surrounding events.")

    return "\n".join(parts)

# ----------------------------------------------------------------------
# Analyze with Gemini or Foundry Local Model
# ----------------------------------------------------------------------
def analyze_with_gemini(events_data, api_key, custom_prompt=None):
    """Send events to Google Gemini API for analysis."""
    if not GEMINI_AVAILABLE:
        return "Gemini library not installed. Run: pip install google-generativeai"
    
    if not api_key:
        return "Gemini API key not provided. Add GEMINI_API_KEY to environment or provide in form."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Prepare event data (limit size)
        try:
            event_data = json.dumps(events_data, indent=2)[:2000]
        except:
            event_data = str(events_data)[:2000]
        
        if custom_prompt:
            user_message = str(custom_prompt) + "\n\nEvents Data:\n" + event_data
        else:
            user_message = f"""You are a Windows system diagnostics assistant. Analyze these event log entries and provide:
- Summary of what these events mean
- Whether they indicate problems
- Possible root causes
- Recommended next steps

Events Data:
{event_data}"""
        
        response = model.generate_content(user_message)
        return response.text if response else "Gemini returned empty response"
    except Exception as e:
        return f"Gemini API error: {str(e)}"

# ----------------------------------------------------------------------
# Analyze with Foundry Local Model
# ----------------------------------------------------------------------
def analyze_with_model(events_data, model_endpoint, model_name, custom_prompt=None):
    """Send events to Microsoft Foundry Local API for analysis."""
    event_data = json.dumps(events_data, indent=2)[:95]  # Limit size for prompt
    # print(event_data)
    if custom_prompt:
        user_message = str(custom_prompt) + "\nEvents Data:" + str(event_data)
    else:
        user_message = f"""You are a Windows system diagnostics assistant. Analyze these event log entries and provide:

                - Summary of what these events mean
                - Whether they indicate problems
                - Possible root causes
                - Recommended next steps

                Events Data:
                {event_data}"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "stream": False
    }

    try:
        # Use longer timeout for model inference (can be slow for large models)
        resp = requests.post(model_endpoint, json=payload, timeout=MODEL_TIMEOUT)
    except req_ex.Timeout as e:
        # Fallback analysis for first event
        fallback = local_fallback_analysis(events_data[0] if isinstance(events_data, list) else events_data)
        return f"Model endpoint timeout ({MODEL_TIMEOUT}s): The model is taking too long to respond.\n\nVerify:\n- Foundry Local is running on {model_endpoint}\n- Model '{model_name}' is loaded\n- System has enough resources\n\nFallback analysis:\n{fallback}"
    except req_ex.ConnectionError as e:
        # Fallback analysis for first event
        fallback = local_fallback_analysis(events_data[0] if isinstance(events_data, list) else events_data)
        return f"Cannot connect to model endpoint: {model_endpoint}\n\nVerify:\n- Foundry Local is running\n- Endpoint is correct (default: http://localhost:50146/v1/chat/completions)\n- No firewall blocking the connection\n\nFallback analysis:\n{fallback}"
    except req_ex.RequestException as e:
        # Fallback analysis for first event
        fallback = local_fallback_analysis(events_data[0] if isinstance(events_data, list) else events_data)
        return f"Model endpoint error: {e}\n\nFallback analysis:\n{fallback}"

    if resp.status_code != 200:
        fallback = local_fallback_analysis(events_data[0] if isinstance(events_data, list) else events_data)
        return f"HTTP {resp.status_code}\n\nFallback analysis:\n{fallback}"

    try:
        data = resp.json()
    except Exception:
        fallback = local_fallback_analysis(events_data[0] if isinstance(events_data, list) else events_data)
        return f"Non-JSON response\n\nFallback analysis:\n{fallback}"

    try:
        if isinstance(data, dict) and "choices" in data:
            choices = data["choices"]
            if isinstance(choices, list) and len(choices) > 0:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                if content:
                    return content
        return "Model returned empty response"
    except Exception as e:
        fallback = local_fallback_analysis(events_data[0] if isinstance(events_data, list) else events_data)
        return f"Parse error: {e}\n\nFallback analysis:\n{fallback}"

# ----------------------------------------------------------------------
# Save Analysis Result
# ----------------------------------------------------------------------
def save_analysis_result(log_type, source_name, event_id, events, analysis):
    """Save analysis result to JSON file."""
    timestamp = datetime.now().isoformat()
    result = {
        "timestamp": timestamp,
        "log_type": log_type,
        "source_name": source_name,
        "event_id": event_id,
        "event_count": len(events) if isinstance(events, list) else 1,
        "events": events,
        "analysis": analysis
    }
    
    filename = DATA_DIR / f"analysis_{timestamp.replace(':', '-')}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    
    return str(filename)


# Flask Routes
@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template('index.html')

# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.route('/api/model-status', methods=['POST'])
def model_status():
    """Check if model endpoint is responding."""
    data = request.json
    model_endpoint = data.get('model_endpoint', DEFAULT_MODEL_ENDPOINT)
    model_name = data.get('model_name', DEFAULT_MODEL_NAME)
    
    try:
        # Quick ping to model with minimal data
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "ping"}
            ],
            "temperature": 0.7,
            "stream": False,
            "max_tokens": 5
        }
        resp = requests.post(model_endpoint, json=payload, timeout=30)
        
        if resp.status_code == 200:
            return jsonify({"status": "ok", "message": "Model is responding"}), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"Model returned HTTP {resp.status_code}",
                "details": resp.text[:200]
            }), 500
    except req_ex.Timeout:
        return jsonify({
            "status": "timeout",
            "message": "Model endpoint is not responding (timeout)",
            "details": "Check if Foundry Local is running on the specified endpoint"
        }), 504
    except req_ex.ConnectionError as e:
        return jsonify({
            "status": "connection_error",
            "message": "Cannot connect to model endpoint",
            "details": str(e)[:200]
        }), 503
    except Exception as e:
        return jsonify({
            "status": "unknown_error",
            "message": "Error checking model status",
            "details": str(e)[:200]
        }), 500

# ----------------------------------------------------------------------
# Event Log API Endpoints
# ----------------------------------------------------------------------
@app.route('/api/log-types')
def get_log_types():
    """Return available event log types."""
    return jsonify({"log_types": EVENTLOG_TYPES})

# ----------------------------------------------------------------------
# Event Source API Endpoint
# ----------------------------------------------------------------------
@app.route('/api/sources/<log_type>')
def get_sources(log_type):
    """Return available source names for a log type."""
    if log_type not in EVENTLOG_TYPES:
        return jsonify({"error": "Invalid log type"}), 400
    
    sources = get_all_event_sources(log_type)
    return jsonify({"sources": sources})


# ----------------------------------------------------------------------
# Event Retrieval API Endpoint
# ----------------------------------------------------------------------
@app.route('/api/events', methods=['POST'])
def get_events():
    """Retrieve events matching criteria."""
    data = request.json
    log_type = data.get('log_type')
    source_name = data.get('source_name')
    event_id = data.get('event_id')
    max_count = data.get('max_count', 100)
    
    if not log_type or log_type not in EVENTLOG_TYPES:
        return jsonify({"error": "Invalid log type"}), 400
    
    events = get_events_by_criteria(log_type, source_name, event_id, max_count)
    return jsonify({"events": events})

# ----------------------------------------------------------------------
# Event Analysis API Endpoint
# ----------------------------------------------------------------------
@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze events with AI model."""
    data = request.json
    log_type = data.get('log_type')
    source_name = data.get('source_name')
    event_id = data.get('event_id')
    custom_prompt = data.get('custom_prompt')
    model_provider = data.get('model_provider', 'foundry')  # 'foundry' or 'gemini'
    model_endpoint = data.get('model_endpoint', DEFAULT_MODEL_ENDPOINT)
    model_name = data.get('model_name', DEFAULT_MODEL_NAME)
    gemini_api_key = data.get('gemini_api_key', GEMINI_API_KEY)
    
    if not log_type or log_type not in EVENTLOG_TYPES:
        return jsonify({"error": "Invalid log type"}), 400
    
    # Get events
    events = get_events_by_criteria(log_type, source_name, event_id, 50)
    
    if not events or (isinstance(events, dict) and "error" in events):
        return jsonify({"error": "No events found matching criteria"}), 400
    
    # Analyze with selected model provider
    if model_provider == 'gemini':
        analysis = analyze_with_gemini(events, gemini_api_key, custom_prompt)
    else:
        analysis = analyze_with_model(events, model_endpoint, model_name, custom_prompt)
    
    # Save result
    result_file = save_analysis_result(log_type, source_name, event_id, events, analysis)
    
    return jsonify({
        "events": events,
        "analysis": analysis,
        "result_file": result_file
    })

# ----------------------------------------------------------------------
# Chat API Endpoint
# ----------------------------------------------------------------------
@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for follow-up questions using retrieved events as context."""
    data = request.json or {}
    model_provider = data.get('model_provider', 'foundry')  # 'foundry' or 'gemini'
    model_endpoint = data.get('model_endpoint', DEFAULT_MODEL_ENDPOINT)
    model_name = data.get('model_name', DEFAULT_MODEL_NAME)
    gemini_api_key = data.get('gemini_api_key', GEMINI_API_KEY)
    events = data.get('events')
    question = data.get('question', '')

    events = events[:95] if events else None  # Limit to first 95 events for context

    if not events or not question:
        return jsonify({"error": "Missing 'events' or 'question' in request"}), 400

    # Build a system message with events as context
    try:
        events_json = json.dumps(events, indent=2)
    except Exception:
        events_json = str(events)

    system_msg = f"You are a Windows system diagnostics assistant. Use the following event log entries as context for answering the user's question. Only reference the events as needed.\n\nEvents Data:\n{events_json}"

    # Route to selected model provider
    if model_provider == 'gemini':
        if not GEMINI_AVAILABLE:
            return jsonify({"error": "Gemini library not installed. Run: pip install google-generativeai"}), 500
        if not gemini_api_key:
            return jsonify({"error": "Gemini API key not provided"}), 400
        
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            user_message = system_msg + "\n\nUser Question: " + question
            response = model.generate_content(user_message)
            reply = response.text if response else "Gemini returned empty response"
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"error": f"Gemini API error: {str(e)}"}), 500
    else:
        # Foundry Local model
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "stream": False
        }

        try:
            resp = requests.post(model_endpoint, json=payload, timeout=MODEL_TIMEOUT)
        except req_ex.Timeout:
            return jsonify({"error": f"Model endpoint timeout ({MODEL_TIMEOUT}s)"}), 504
        except req_ex.ConnectionError as e:
            return jsonify({"error": f"Cannot connect to model endpoint: {e}"}), 503
        except req_ex.RequestException as e:
            return jsonify({"error": f"Request error: {e}"}), 500

        if resp.status_code != 200:
            return jsonify({"error": f"Model returned HTTP {resp.status_code}", "details": resp.text[:200]}), 500

        try:
            resp_data = resp.json()
        except Exception:
            return jsonify({"error": "Non-JSON response from model"}), 500

        try:
            if isinstance(resp_data, dict) and "choices" in resp_data:
                choices = resp_data["choices"]
                if isinstance(choices, list) and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    return jsonify({"reply": content})
            return jsonify({"reply": ""})
        except Exception as e:
            return jsonify({"error": f"Parse error: {e}"}), 500
# ----------------------------------------------------------------------
# Results API Endpoints
# ----------------------------------------------------------------------    
@app.route('/api/results')
def get_results():
    """List all saved analysis results."""
    results = []
    for file in sorted(DATA_DIR.glob('*.json'), reverse=True):
        with open(file, 'r') as f:
            result = json.load(f)
            result['filename'] = file.name
            results.append(result)
    return jsonify({"results": results})


# ----------------------------------------------------------------------
# Results API Endpoints
# ----------------------------------------------------------------------
@app.route('/api/results/<filename>')
def get_result(filename):
    """Get a specific analysis result."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "Result not found"}), 404
    
    with open(filepath, 'r') as f:
        result = json.load(f)
    
    return jsonify(result)


# ----------------------------------------------------------------------
# Run the Flask app
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
