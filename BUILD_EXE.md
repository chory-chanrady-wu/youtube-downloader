# Building YouTube Downloader as .exe

There are two approaches to run this as an executable on Windows:

## Option A: Single .exe file (Recommended for end users)

This creates a standalone `YouTubeDownloader.exe` (~250-350 MB) that runs everywhere.

### Prerequisites
- Python 3.10+ installed
- ffmpeg installed and on PATH
- PyInstaller (`pip install pyinstaller`)

### Build steps

#### 1) Open PowerShell in the project folder

```powershell
Set-Location "C:\Users\CHORY Chanrady\Desktop\Tools\youtube"
```

#### 2) Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

#### 3) Install PyInstaller

```powershell
pip install pyinstaller
```

#### 4) Run the build script

```powershell
python build_exe.py
```

This will take 1-2 minutes. You'll see output like:

```
📦 Building .exe with PyInstaller...
✅ Building .exe with PyInstaller complete

✅ Success! .exe created at:
   C:\Users\CHORY Chanrady\Desktop\Tools\youtube\dist\YouTubeDownloader.exe

📦 File size: 26.1 MB

🚀 Run it with: YouTubeDownloader.exe
```

#### 5) Find your .exe

The executable is in:
```
C:\Users\CHORY Chanrady\Desktop\Tools\youtube\dist\YouTubeDownloader.exe
```

You can:
- **Copy it anywhere** on Windows
- **Share it** with others (no installation needed)
- **Create a shortcut** on your desktop

#### 6) Run it

Double-click `YouTubeDownloader.exe` and the browser will open automatically.

---

## Option B: Batch launcher (Lightweight)

This creates a `run.bat` file (~2 KB) that launches the app without a big .exe.

### Prerequisites
- Python 3.10+ installed
- ffmpeg installed and on PATH

### Usage

Just double-click **`run.bat`** in the project folder.

It will:
1. Create a virtual environment (if needed)
2. Install dependencies
3. Start the server
4. Open your browser

**Pros:**
- Tiny file size
- Easy to share the batch file
- Auto-updates when you pull new code

**Cons:**
- Requires Python installed on the user's machine
- Slower first startup

---

## Requirements for both

### ffmpeg (required for MP3)

Install on Windows:

**Option 1: winget**
```powershell
winget install gyan.ffmpeg
```

**Option 2: Scoop**
```powershell
scoop install ffmpeg
```

**Option 3: Chocolatey** (admin required)
```powershell
choco install ffmpeg -y
```

Verify:
```powershell
ffmpeg -version
```

---

## Troubleshooting

### .exe won't start
- Make sure all dependencies installed with no errors
- Check that ffmpeg is on PATH: `ffmpeg -version`
- Try running `launcher.py` directly to see error messages:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  python launcher.py
  ```

### .bat says "Python not found"
- Install Python from https://www.python.org/downloads
- Make sure to check **"Add Python to PATH"** during installation
- Restart PowerShell/Command Prompt after installing

### MP3 downloads fail
- Install ffmpeg (see above)
- After installing, close and reopen the browser

### File size is too large
- The .exe includes all dependencies (ffmpeg, Python runtime, libraries)
- Use Option B (batch launcher) if size matters
- Or distribute just the .bat file instead

---


## Distributing to others

**With Option A (.exe):**
1. Build the .exe
2. Upload `dist/YouTubeDownloader.exe`
3. Users just download and run

**With Option B (.bat):**
1. Share the entire project folder, or just:
   - `run.bat`
   - `requirements.txt`
   - `launcher.py`
   - `app/` folder
2. Users run `run.bat` (requires Python 3.10+ installed)

---

## Next steps

1. Pick Option A or B
2. Follow the build steps above
3. Test the .exe or .bat locally
4. Share with others or deploy

Questions? Check the main `README.md` for environment variables and configuration.

