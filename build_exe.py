#!/usr/bin/env python3
"""
Build script for creating a standalone .exe using PyInstaller.
Run: python build_exe.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n[BUILD] {description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[ERROR] {description} failed!")
        sys.exit(1)
    print(f"[OK] {description} complete")

def main():
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Optional icon file
    icon_path = project_root / "app" / "static" / "icon.ico"
    icon_arg = f"--icon={icon_path} " if icon_path.exists() else ""

    # Build command for PyInstaller
    # The key is bundling the app folder and static/template files
    pyinstaller_cmd = (
        "pyinstaller "
        "--onefile "  # Single .exe file
        "--name=YouTubeDownloader "
        f"{icon_arg}"
        "--add-data=app/templates:app/templates "
        "--add-data=app/static:app/static "
        "--hidden-import=uvicorn.lifespan.on "
        "--hidden-import=uvicorn.loops "
        "--hidden-import=uvicorn.loops.auto "
        "--hidden-import=uvicorn.protocols "
        "--hidden-import=uvicorn.protocols.http "
        "--hidden-import=uvicorn.protocols.http.auto "
        "--hidden-import=uvicorn.protocols.websocket "
        "--hidden-import=uvicorn.protocols.websocket.auto "
        "--collect-all=fastapi "
        "--collect-all=starlette "
        "--collect-all=jinja2 "
        "launcher.py"
    )

    run_command(pyinstaller_cmd, "Building .exe with PyInstaller")

    exe_path = project_root / "dist" / "YouTubeDownloader.exe"
    if exe_path.exists():
        print(f"\n[OK] Success! .exe created at:\n   {exe_path}")
        print(f"\n[INFO] File size: {exe_path.stat().st_size / (1024**2):.1f} MB")
        print("\n[INFO] Run it with: YouTubeDownloader.exe")
    else:
        print(f"\n[ERROR] .exe not found at {exe_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()

