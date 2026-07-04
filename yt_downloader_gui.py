# yt_downloader_gui.py
# 2026 [ ivan deus ]
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import json
import re
import os
import threading
import glob
import shutil
import string
import random

class YTDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader & Merger GUI")
        self.root.geometry("850x650")
        self.root.minsize(700, 500)
        
        # Handle graceful closing to kill background processes
        self.current_process = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Store the video title
        self.video_title = "YouTube_Video"
        
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
                
        # NEW: Resolve executables in system PATH to absolute paths
        # This is crucial for yt-dlp's --ffmpeg-location which expects a valid path
        for exe_attr in ['ytdlp_path', 'ffmpeg_path']:
            path = getattr(self, exe_attr)
            if not os.path.isabs(path) and not os.path.exists(path):
                resolved = shutil.which(path)
                if resolved:
                    setattr(self, exe_attr, resolved)
                else:
                    # Fallback to non-.exe name for Linux/Mac
                    fallback_name = "yt-dlp" if "ytdlp" in exe_attr else "ffmpeg"
                    resolved = shutil.which(fallback_name)
                    if resolved: setattr(self, exe_attr, resolved)
                    
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
        
        # NEW: Disable download buttons if the user types a new URL
        self.url_entry.bind("<KeyRelease>", lambda e: self.on_url_change())
        
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
        
        # --- Action Buttons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(0, 10))
        
        self.download_btn = ttk.Button(btn_frame, text="Download & Merge", command=self.start_download, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.audio_btn = ttk.Button(btn_frame, text="Download Audio Only", command=self.start_audio_download, state=tk.DISABLED)
        self.audio_btn.pack(side=tk.LEFT, padx=5)
        
        # --- Log Area ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def on_url_change(self):
        """Disables download buttons when URL is changed to prevent stale format selection."""
        self.download_btn.config(state=tk.DISABLED)
        self.audio_btn.config(state=tk.DISABLED)

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
            try:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except tk.TclError:
                pass # Window was closed
        self.root.after(0, _update)

    def update_progress(self, percent, status_text=""):
        def _update():
            try:
                self.progress['value'] = percent
                if status_text:
                    self.status_var.set(status_text)
            except tk.TclError:
                pass
        self.root.after(0, _update)
        
    def update_status(self, text):
        def _update():
            try:
                self.status_var.set(text)
            except tk.TclError:
                pass
        self.root.after(0, _update)

    def sanitize_filename(self, filename):
        """Removes illegal characters and truncates the filename for safety."""
        # FIXED: Added % to prevent yt-dlp template parsing errors
        clean_name = re.sub(r'[\\/*?:"<>|%]', "", filename).strip()
        clean_name = clean_name[:100] if clean_name else "YouTube_Video"
        return clean_name

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
                cmd = [self.ytdlp_path, "--dump-single-json", "--no-playlist", "--no-warnings", url]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode != 0:
                    self.log(f"Error fetching formats: {result.stderr}")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to fetch formats. Check log."))
                    return

                data = json.loads(result.stdout)
                
                self.video_title = data.get('title', 'YouTube_Video')
                self.log(f"Video Title: {self.video_title}")
                
                formats = data.get('formats', [])
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
        self.audio_btn.config(state=tk.NORMAL)
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
        
        safe_title = self.sanitize_filename(self.video_title)
        
        # --- FIX FOR FFMPEG NON-ASCII PATH ISSUES ---
        # Create a temporary ASCII-only folder inside the current working directory.
        # This prevents ffmpeg from failing when the final filename contains Cyrillic/special characters.
        temp_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        temp_dir = os.path.join(os.getcwd(), f"ytdlp_{temp_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Template for yt-dlp output in the temp directory
        temp_final_template = os.path.join(temp_dir, "merged_video.%(ext)s")
        
        self.download_btn.config(state=tk.DISABLED)
        self.audio_btn.config(state=tk.DISABLED)
        self.fetch_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        def run_download():
            try:
                has_audio = selected_format.get('acodec') != 'none'
                
                if has_audio:
                    self.update_status("Downloading video with audio...")
                    self.log(f"Selected format {format_id} has audio. Downloading directly...")
                    cmd = [self.ytdlp_path, "-f", format_id, "-o", temp_final_template, "--no-warnings", url]
                    self.run_command(cmd, is_download=True)
                else:
                    self.update_status("Downloading and merging video + audio...")
                    self.log(f"Downloading video (format {format_id}) and best available audio...")
                    
                    # FIXED: Let yt-dlp handle the merging automatically using --ffmpeg-location
                    cmd = [
                        self.ytdlp_path, 
                        "-f", f"{format_id}+ba/b", 
                        "-o", temp_final_template,
                        "--ffmpeg-location", self.ffmpeg_path,
                        "--no-warnings", 
                        url
                    ]
                    self.run_command(cmd, is_download=True)
                    
                # After successful download/merge, find the final file in the temp directory
                possible_final_files = glob.glob(os.path.join(temp_dir, "merged_video.*"))
                # Filter out partial downloads (e.g., merged_video.f136.mp4)
                final_files = [f for f in possible_final_files if re.match(r'merged_video\.\w+$', os.path.basename(f))]
                
                if final_files:
                    downloaded_file = final_files[0]
                    ext = os.path.splitext(downloaded_file)[1]
                    final_path = os.path.join(out_dir, f"{safe_title}{ext}")
                    
                    # Clean up old final file if it exists
                    if os.path.exists(final_path):
                        try: os.remove(final_path)
                        except: pass
                        
                    # Move the file to the final destination (Python handles Unicode paths perfectly)
                    shutil.move(downloaded_file, final_path)
                    self.log(f"Successfully moved file to: {final_path}")
                else:
                    raise Exception("Download/Merge failed or final file not found. Check log for errors.")
                
                self.progress['value'] = 100
                self.log("Temporary files cleaned up automatically.")
                
                self.log(f"Success! Saved to: {final_path}")
                self.update_status("Completed!")
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Download completed!\nSaved to:\n{final_path}"))
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
                self.update_status("Error occurred.")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                # Clean up the temporary directory
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
                self.root.after(0, self.reset_ui)

        threading.Thread(target=run_download, daemon=True).start()

    def start_audio_download(self):
        url = self.url_entry.get().strip()
        out_dir = self.out_dir.get()
        
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL.")
            return

        safe_title = self.sanitize_filename(self.video_title)
        audio_final_path = os.path.join(out_dir, f"{safe_title}_audio.%(ext)s")
        
        for p in glob.glob(os.path.join(out_dir, f"{safe_title}_audio.*")):
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        self.download_btn.config(state=tk.DISABLED)
        self.audio_btn.config(state=tk.DISABLED)
        self.fetch_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        def run_audio_download():
            try:
                self.update_status("Downloading best audio...")
                self.log("Extracting best audio track...")
                
                cmd = [
                    self.ytdlp_path, 
                    "-f", "bestaudio", 
                    "-o", audio_final_path, 
                    "--no-warnings", 
                    url
                ]
                self.run_command(cmd, is_download=True)
                
                actual_files = glob.glob(os.path.join(out_dir, f"{safe_title}_audio.*"))
                if actual_files:
                    final_file = actual_files[0]
                    self.log(f"Success! Saved to: {final_file}")
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Audio download completed!\nSaved to:\n{final_file}"))
                else:
                    self.log("Warning: Download finished, but couldn't locate the final file.")
                    
                self.update_status("Completed!")
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
                self.update_status("Error occurred.")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self.reset_ui)

        threading.Thread(target=run_audio_download, daemon=True).start()

    def run_command(self, cmd, is_download=False):
        self.log(f"Executing: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=False, 
            bufsize=0
        )
        self.current_process = process
        
        buffer = ""
        while True:
            try:
                # FIXED: Pythonic stream reading
                chunk = process.stdout.read(4096)
                if not chunk:
                    if process.poll() is not None: break
                    continue
                buffer += chunk.decode('utf-8', errors='replace')
            except (OSError, ValueError):
                break
                
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
                            continue 
                            
                    if "frame=" in line and "time=" in line:
                        time_match = re.search(r'time=([\d:.]+)', line)
                        speed_match = re.search(r'speed=\s*([\d.]+x)', line)
                        status = f"Merging: {time_match.group(1) if time_match else ''}"
                        if speed_match: status += f" @ {speed_match.group(1)}"
                        self.update_status(status)
                        continue
                        
                    self.log(line) 
                    
        if buffer.strip():
            self.log(buffer.strip())
            
        process.wait()
        self.current_process = None
        if process.returncode != 0:
            raise Exception(f"Command failed with return code {process.returncode}")

    def reset_ui(self):
        self.download_btn.config(state=tk.NORMAL)
        self.audio_btn.config(state=tk.NORMAL)
        self.fetch_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDownloaderApp(root)
    root.mainloop()
