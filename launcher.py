#!/usr/bin/env python3
"""
Launcher for the YouTube Downloader .exe
This is the entry point that PyInstaller uses.
"""

import sys
import webbrowser
from pathlib import Path
from threading import Thread
import time
import logging

def main():
    # Try to auto-open the browser, but don't block if it fails
    def open_browser():
        time.sleep(2)  # Give uvicorn time to start
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except Exception:
            pass

    # Start browser in background thread
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Configure basic logging to avoid uvicorn config errors
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Import and run uvicorn
    import uvicorn
    from app.main import app

    print("\n" + "=" * 60)
    print("🎬 YouTube Downloader")
    print("=" * 60)
    print("\n✅ Server running at http://127.0.0.1:8000")
    print("📱 Opening browser...\n")
    print("Press Ctrl+C to stop the server.\n")

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()

