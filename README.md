# YouTube Video Downloader GUI 🎬 
![yt_downloader_gui.py](https://github.com/IvanDeus/YouTube-video-downloader-py/blob/main/yt-downloader.jpg)
# YouTube-video-downloader-py

A user-friendly, graphical desktop application for downloading and merging YouTube videos. Built with **Python** and **Tkinter**, this tool replaces the need for complex command-line interfaces by providing a visual format selector, real-time progress tracking, and automatic audio/video merging.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## ✨ Features

- 🎨 **Modern GUI**: Clean, responsive, and intuitive Tkinter interface.
- 📊 **Visual Format Selection**: Fetches and displays available video qualities (Resolution, FPS, File Size) in an easy-to-read, sortable table.
- 🔄 **Smart Auto-Merging**: Intelligently detects if your selected video format already includes audio. If it doesn't, it automatically downloads the best available audio and merges them using FFmpeg.
- 📈 **Real-Time Progress**: Live progress bar and status updates showing download speed, percentage, and ETA.
- 🧹 **Auto-Cleanup**: Automatically deletes temporary intermediate files (`video_temp.*`, `audio_temp.*`) after a successful merge.
- 🛑 **Graceful Exit**: Safely kills background `yt-dlp` or `ffmpeg` processes if you close the window mid-download.
- 📂 **Custom Save Location**: Browse and choose exactly where you want your downloaded videos to be saved.

---

## 📋 Prerequisites

Before running the application, ensure you have the following:

1. **[Python 3.14+](https://www.python.org/downloads/)** (No external Python packages are required; it uses built-in `tkinter`).
2. **[yt-dlp](https://github.com/yt-dlp/yt-dlp#release-files)**: The core engine for downloading.
3. **[FFmpeg](https://ffmpeg.org/)**: Required for merging separate video and audio streams.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/IvanDeus/YouTube-video-downloader-py.git
cd YouTube-video-downloader-py
```

### 2. Set up Dependencies (yt-dlp & FFmpeg)
The script is designed to automatically detect `yt-dlp` and `ffmpeg` if they are placed in the same directory.

**Option A: Local Executables (Recommended for Windows)**
- Download the latest `yt-dlp.exe` from the [yt-dlp releases page](https://github.com/yt-dlp/yt-dlp/releases) and place it in the project folder.
- Download a static FFmpeg build (e.g., from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)), extract it, and place the `ffmpeg` folder (containing the `bin` folder) in the project directory.

*Your folder structure should look like this:*
```text
YouTube-video-downloader-py/
├── yt_downloader_gui.py
├── yt-dlp.exe
└── ffmpeg/
    └── bin/
        └── ffmpeg.exe
```

**Option B: System PATH**
If you prefer, you can install `yt-dlp` and `ffmpeg` globally and add them to your system's `PATH`. The script will fall back to using the system commands if local executables are not found.

---

## 💻 Usage

1. **Run the Application!** Click on it or type in a terminal:
   ```bash
   python yt_downloader_gui.py
   ```

2. **Fetch Formats**:
   - Paste a YouTube video URL into the top input field.
   - Click the **Fetch Formats** button. The app will query YouTube and populate the table with available video qualities.

3. **Select Quality**:
   - Click on your desired resolution/quality in the table (e.g., `1080p`, `720p`).
   - *Note: The app automatically handles the logic of whether that format needs a separate audio download.*

4. **Choose Save Location**:
   - By default, it saves to the current directory. Click **Browse** to choose a specific folder.

5. **Download & Merge**:
   - Click the **Download & Merge** button.
   - Watch the real-time progress bar and log output. Once finished, a success popup will appear, and your final video will be ready!

---

## 🛠️ Troubleshooting

### "WARNING: No supported JavaScript runtime could be found"
This is a warning from `yt-dlp` regarding YouTube's JavaScript-based signatures. It usually **does not** break the download. If you encounter missing formats or errors, you can fix this by installing a JS runtime like [Deno](https://deno.land/) or [Node.js](https://nodejs.org/) and adding it to your system PATH.

### FFmpeg Not Found / Merge Fails
Ensure that `ffmpeg.exe` is correctly placed in the `ffmpeg/bin/` directory, or that `ffmpeg` is added to your system's environment variables (PATH). The app relies on FFmpeg to mux the video and audio streams together.

### GUI Freezes
The app runs all downloads in background threads. If the GUI ever freezes, it is likely due to a network timeout or a blocked subprocess. You can safely close the window, and the app will automatically kill the background processes.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---
2026 [ ivan deus ]
