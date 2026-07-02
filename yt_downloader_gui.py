# yt_downloader_gui.py
# 2026 [ ivan deus ]
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import json
import re
import os
import threading
import sys
import glob

class YTDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader & Merger GUI")
        self.root.geometry("850x650")
        self.root.minsize(700, 500)
        
        # Handle graceful closing to kill background processes
        self.current_process = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-detect executable paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.ytdlp_path = os.path.join(script_dir, "yt-dlp.exe")
        if not os.path.exists(self.ytdlp_path):
            self.ytdlp_path = "yt-dlp.exe" # Fallback to PATH
            
        self.ffmpeg_path = os.path.join(script_dir, "ffmpeg", "bin", "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = os.path.join(script_dir, "ffmpeg.exe")
            if not os.path.exists(self.ffmpeg_path):
                self.ffmpeg_path = "ffmpeg" # Fallback to PATH
                
        self.formats_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        # Use a modern theme if available
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- URL Input ---
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="YouTube URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.fetch_btn = ttk.Button(url_frame, text="Fetch Formats", command=self.fetch_formats)
        self.fetch_btn.pack(side=tk.LEFT)
        
        # --- Format Selection Table ---
        format_frame = ttk.LabelFrame(main_frame, text="Select Video Quality", padding=10)
        format_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("id", "resolution", "fps", "filesize", "note")
        self.format_tree = ttk.Treeview(format_frame, columns=columns, show="headings", height=8)
        
        self.format_tree.heading("id", text="ID")
        self.format_tree.heading("resolution", text="Resolution")
        self.format_tree.heading("fps", text="FPS")
        self.format_tree.heading("filesize", text="File Size")
        self.format_tree.heading("note", text="Note")
        
        self.format_tree.column("id", width=50, anchor=tk.CENTER)
        self.format_tree.column("resolution", width=120, anchor=tk.CENTER)
        self.format_tree.column("fps", width=60, anchor=tk.CENTER)
        self.format_tree.column("filesize", width=100, anchor=tk.CENTER)
        self.format_tree.column("note", width=250)
        
        scrollbar = ttk.Scrollbar(format_frame, orient=tk.VERTICAL, command=self.format_tree.yview)
        self.format_tree.configure(yscroll=scrollbar.set)
        
        self.format_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- Output Directory ---
        out_frame = ttk.Frame(main_frame)
        out_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(out_frame, text="Save to:").pack(side=tk.LEFT)
        self.out_dir = tk.StringVar(value=os.getcwd())
        self.out_entry = ttk.Entry(out_frame, textvariable=self.out_dir, width=60)
        self.out_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.browse_btn = ttk.Button(out_frame, text="Browse", command=self.browse_dir)
        self.browse_btn.pack(side=tk.LEFT)
        
        # --- Status and Progress Bar ---
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # --- Action Button ---
        self.download_btn = ttk.Button(main_frame, text="Download & Merge", command=self.start_download, state=tk.DISABLED)
        self.download_btn.pack(pady=(0, 10))
        
        # --- Log Area ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def on_closing(self):
        if self.current_process and self.current_process.poll() is None:
            try: self.current_process.kill()
            except: pass
        self.root.destroy()

    def browse_dir(self):
        directory = filedialog.askdirectory(initialdir=self.out_dir.get())
        if directory:
            self.out_dir.set(directory)

    def log(self, message):
        def _update():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _update)

    def update_progress(self, percent, status_text=""):
        def _update():
            self.progress['value'] = percent
            if status_text:
                self.status_var.set(status_text)
        self.root.after(0, _update)
        
    def update_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def fetch_formats(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL.")
            return
            
        self.fetch_btn.config(state=tk.DISABLED)
        self.update_status("Fetching formats...")
        self.log("Fetching available formats...")
        
        def run_fetch():
            try:
                # Use JSON dump for easy parsing, suppress warnings to keep log clean
                cmd = [self.ytdlp_path, "--dump-single-json", "--no-playlist", "--no-warnings", url]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode != 0:
                    self.log(f"Error fetching formats: {result.stderr}")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to fetch formats. Check log."))
                    return

                data = json.loads(result.stdout)
                formats = data.get('formats', [])
                
                # Filter for formats that actually have video
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                self.root.after(0, self.populate_formats, video_formats)
                
            except Exception as e:
                self.log(f"Exception: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))

        threading.Thread(target=run_fetch, daemon=True).start()

    def populate_formats(self, formats):
        for item in self.format_tree.get_children():
            self.format_tree.delete(item)
            
        self.formats_data = {str(f.get('format_id')): f for f in formats}
        
        if not formats:
            self.log("No video formats found.")
            self.update_status("No formats found.")
            return
            
        # Sort by resolution height (descending)
        formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
        
        for f in formats:
            fsize = f.get('filesize') or f.get('filesize_approx')
            fsize_str = f"{fsize / (1024*1024):.2f} MB" if fsize else "N/A"
                
            values = (
                f.get('format_id'),
                f.get('resolution', 'N/A'),
                f.get('fps', 'N/A'),
                fsize_str,
                f.get('format_note', '')
            )
            self.format_tree.insert("", tk.END, values=values)
            
        self.download_btn.config(state=tk.NORMAL)
        self.update_status(f"Found {len(formats)} formats. Select one to download.")
        self.log(f"Found {len(formats)} video formats.")

    def start_download(self):
        selected = self.format_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a video format.")
            return
            
        item = self.format_tree.item(selected[0])
        format_id = str(item['values'][0])
        selected_format = self.formats_data.get(format_id)
        
        url = self.url_entry.get().strip()
        out_dir = self.out_dir.get()
        
        # Use templates so yt-dlp can choose the correct extension
        video_path_template = os.path.join(out_dir, "video_temp.%(ext)s")
        audio_path_template = os.path.join(out_dir, "audio_temp.%(ext)s")
        final_path = os.path.join(out_dir, "final_video.mp4")
        
        # Clean up old temp files
        for p in glob.glob(os.path.join(out_dir, "video_temp.*")) + \
                 glob.glob(os.path.join(out_dir, "audio_temp.*")) + \
                 [final_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        self.download_btn.config(state=tk.DISABLED)
        self.fetch_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        def run_download():
            try:
                has_audio = selected_format.get('acodec') != 'none'
                
                if has_audio:
                    self.update_status("Downloading video with audio...")
                    self.log(f"Selected format {format_id} has audio. Downloading directly...")
                    cmd = [self.ytdlp_path, "-f", format_id, "-o", final_path, "--no-warnings", url]
                    self.run_command(cmd, is_download=True)
                else:
                    self.update_status("Downloading video...")
                    self.log(f"Downloading video (format {format_id})...")
                    cmd_v = [self.ytdlp_path, "-f", format_id, "-o", video_path_template, "--no-warnings", url]
                    self.run_command(cmd_v, is_download=True)
                    
                    video_files = glob.glob(os.path.join(out_dir, "video_temp.*"))
                    if not video_files: raise Exception("Video download failed, file not found.")
                    video_path = video_files[0]
                    
                    self.update_status("Downloading audio...")
                    self.progress['value'] = 0 # Reset for audio
                    self.log("Downloading audio (format 140/bestaudio)...")
                    cmd_a = [self.ytdlp_path, "-f", "140/bestaudio", "-o", audio_path_template, "--no-warnings", url]
                    self.run_command(cmd_a, is_download=True)
                    
                    audio_files = glob.glob(os.path.join(out_dir, "audio_temp.*"))
                    if not audio_files: raise Exception("Audio download failed, file not found.")
                    audio_path = audio_files[0]
                    
                    self.update_status("Merging video and audio...")
                    self.progress.config(mode='indeterminate')
                    self.progress.start(10)
                    self.log("Merging video and audio...")
                    cmd_merge = [
                        self.ffmpeg_path, "-i", video_path, "-i", audio_path,
                        "-c:v", "copy", "-c:a", "aac", "-strict", "experimental",
                        "-y", final_path
                    ]
                    self.run_command(cmd_merge, is_download=False)
                    
                    self.progress.stop()
                    self.progress.config(mode='determinate')
                    self.progress['value'] = 100
                    
                    if os.path.exists(final_path):
                        for p in [video_path, audio_path]:
                            try: os.remove(p)
                            except: pass
                        self.log("Temporary files cleaned up.")
                
                self.log(f"Success! Saved to: {final_path}")
                self.update_status("Completed!")
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Download completed!\nSaved to:\n{final_path}"))
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
                self.update_status("Error occurred.")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self.reset_ui)

        threading.Thread(target=run_download, daemon=True).start()

    def run_command(self, cmd, is_download=False):
        self.log(f"Executing: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=False, # Handle decoding manually for real-time reading
            bufsize=0
        )
        self.current_process = process
        
        buffer = ""
        while True:
            try:
                # Read raw bytes to avoid blocking on line-endings
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    if process.poll() is not None: break
                    continue
                buffer += chunk.decode('utf-8', errors='replace')
            except OSError:
                break
                
            # Process buffer line-by-line (handling both \r and \n)
            while '\r' in buffer or '\n' in buffer:
                idx_r = buffer.find('\r')
                idx_n = buffer.find('\n')
                
                if idx_r == -1 and idx_n == -1: break
                    
                if idx_r != -1 and (idx_n == -1 or idx_r < idx_n):
                    line = buffer[:idx_r]
                    buffer = buffer[idx_r+1:]
                else:
                    line = buffer[:idx_n]
                    buffer = buffer[idx_n+1:]
                    
                line = line.strip()
                if line:
                    # Parse yt-dlp progress
                    if is_download and "[download]" in line:
                        match = re.search(r'\[download\]\s+([\d.]+)%', line)
                        if match:
                            percent = float(match.group(1))
                            speed_match = re.search(r'at\s+([\d.]+\w+/s)', line)
                            eta_match = re.search(r'ETA\s+([\d:]+)', line)
                            status = f"Downloading: {percent}%"
                            if speed_match: status += f" @ {speed_match.group(1)}"
                            if eta_match: status += f" (ETA {eta_match.group(1)})"
                            
                            self.update_progress(percent, status)
                            continue # Don't spam the log with every % update
                            
                    # Parse ffmpeg progress
                    if "frame=" in line and "time=" in line:
                        time_match = re.search(r'time=([\d:.]+)', line)
                        speed_match = re.search(r'speed=\s*([\d.]+x)', line)
                        status = f"Merging: {time_match.group(1) if time_match else ''}"
                        if speed_match: status += f" @ {speed_match.group(1)}"
                        self.update_status(status)
                        continue
                        
                    self.log(line) # Log other important events
                    
        if buffer.strip():
            self.log(buffer.strip())
            
        process.wait()
        self.current_process = None
        if process.returncode != 0:
            raise Exception(f"Command failed with return code {process.returncode}")

    def reset_ui(self):
        self.download_btn.config(state=tk.NORMAL)
        self.fetch_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDownloaderApp(root)
    root.mainloop()
