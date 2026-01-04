import sys

# Check if required modules are available
required_modules = ['flask', 'win32evtlog', 'win32evtlogutil', 'requests']

for module in required_modules:
    try:
        __import__(module)
        print(f"✓ {module} is installed")
    except ImportError:
        print(f"✗ {module} is NOT installed")

print(f"\nPython version: {sys.version}")
print(f"Python executable: {sys.executable}")
