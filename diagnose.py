#!/usr/bin/env python3
"""
Diagnostic tool for Foundry Local connection and configuration
"""

import requests
import sys
import json
from requests import exceptions as req_ex

# Configuration
FOUNDRY_HOST = "localhost"
FOUNDRY_PORT = 50146
FOUNDRY_BASE_URL = f"http://{FOUNDRY_HOST}:{FOUNDRY_PORT}"

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(test_name, success, message=""):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"       {message}")

def test_connection():
    """Test basic connection to Foundry Local"""
    print_header("1. Testing Connection")
    
    try:
        response = requests.get(f"{FOUNDRY_BASE_URL}/openai/status", timeout=5)
        if response.status_code == 200:
            print_status("Connection", True, "Foundry Local is accessible")
            data = response.json()
            print(f"       Endpoints: {data.get('Endpoints', [])}")
            print(f"       Model Dir: {data.get('ModelDirPath', 'N/A')}")
            return True
        else:
            print_status("Connection", False, f"HTTP {response.status_code}")
            return False
    except req_ex.ConnectionError as e:
        print_status("Connection", False, f"Connection refused: {FOUNDRY_BASE_URL}")
        print(f"       Make sure Foundry Local is running on port {FOUNDRY_PORT}")
        return False
    except req_ex.Timeout:
        print_status("Connection", False, "Connection timeout")
        return False
    except Exception as e:
        print_status("Connection", False, str(e))
        return False

def get_available_models():
    """Get list of available models"""
    print_header("2. Available Models")
    
    try:
        response = requests.get(f"{FOUNDRY_BASE_URL}/openai/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            if isinstance(models, list):
                print_status("Model List", True, f"Found {len(models)} model(s)")
                for model in models:
                    print(f"       • {model}")
                return models
            else:
                print_status("Model List", False, "Unexpected response format")
                return []
        else:
            print_status("Model List", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        print_status("Model List", False, str(e))
        return []

def test_model_inference(model_name):
    """Test model inference with a simple prompt"""
    print_header("3. Testing Model Inference")
    
    print(f"Testing model: {model_name}")
    print(f"Endpoint: {FOUNDRY_BASE_URL}/v1/chat/completions")
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Respond with 'OK' only."}
        ],
        "temperature": 0.7,
        "stream": False,
        "max_tokens": 10
    }
    
    try:
        print("Sending request... (this may take a moment)")
        response = requests.post(
            f"{FOUNDRY_BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                print_status("Inference", True, f"Model responded: '{content.strip()}'")
                print(f"       Tokens - Prompt: {usage.get('prompt_tokens')}, Completion: {usage.get('completion_tokens')}")
                return True
            else:
                print_status("Inference", False, "Invalid response format")
                return False
        else:
            print_status("Inference", False, f"HTTP {response.status_code}")
            print(f"       Response: {response.text[:200]}")
            return False
    except req_ex.Timeout:
        print_status("Inference", False, "Timeout (model took too long to respond)")
        print(f"       Try increasing timeout or check if model is loaded")
        return False
    except req_ex.ConnectionError as e:
        print_status("Inference", False, f"Connection error: {e}")
        return False
    except Exception as e:
        print_status("Inference", False, str(e))
        print(f"       Full error: {response.text if 'response' in locals() else str(e)}")
        return False

def test_catalog():
    """Get Foundry catalog information"""
    print_header("4. Foundry Catalog")
    
    try:
        response = requests.get(f"{FOUNDRY_BASE_URL}/foundry/list", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print_status("Catalog Access", True, f"Found {len(models)} model(s) in catalog")
            for model in models[:5]:  # Show first 5
                print(f"       • {model.get('name', 'Unknown')}")
            if len(models) > 5:
                print(f"       ... and {len(models) - 5} more")
            return True
        else:
            print_status("Catalog Access", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("Catalog Access", False, str(e))
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("  FOUNDRY LOCAL DIAGNOSTIC TOOL")
    print("="*60)
    print(f"Target: {FOUNDRY_BASE_URL}")
    
    # Test 1: Connection
    if not test_connection():
        print("\n" + "!"*60)
        print("  Cannot connect to Foundry Local!")
        print("!"*60)
        print("\nFix:")
        print("1. Start Foundry Local:")
        print("   foundry-local start")
        print("\n2. Or check if it's running on different port:")
        print("   netstat -an | findstr LISTEN")
        print("\n3. Verify Foundry Local documentation:")
        print("   https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/")
        sys.exit(1)
    
    # Test 2: Get available models
    models = get_available_models()
    
    if not models:
        print("\n" + "!"*60)
        print("  No models available!")
        print("!"*60)
        print("\nFix:")
        print("1. Download a model:")
        print("   curl -X POST http://localhost:5272/openai/download \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{")
        print("       \"model\": {")
        print("         \"Uri\": \"azureml://registries/azureml/models/Phi-4-mini-instruct-generic-cpu/versions/4\",")
        print("         \"Name\": \"Phi-4-mini-instruct-generic-cpu\"")
        print("       }")
        print("     }'")
        sys.exit(1)
    
    # Test 3: Test inference with first available model
    model_to_test = models[0] if models else "Phi-4-mini-instruct-generic-cpu"
    test_model_inference(model_to_test)
    
    # Test 4: Catalog
    test_catalog()
    
    print_header("Summary")
    print("✓ Foundry Local is ready to use!")
    print(f"\nUse this in your app.py:")
    print(f"  DEFAULT_MODEL_ENDPOINT = \"http://localhost:50146/v1/chat/completions\"")
    print(f"  DEFAULT_MODEL_NAME = \"{model_to_test}\"")

if __name__ == "__main__":
    main()
