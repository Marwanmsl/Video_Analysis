import os
import tkinter as tk
from tkinter import filedialog, messagebox
import vlc
import threading
import time

VIDEO_FOLDER = "videos"
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

class VideoPlayer:
    def __init__(self, root):
        self.video_list = None
        self.root = root
        self.root.title("Video Analysis")
        self.root.geometry("1080x500")
        # self.root.config(bg="gray")
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        self.video_path = None
        self.is_paused = False
        self.is_muted = False
        self.is_seeking = False
        self.video_list_visible = True

        # Main Layout: Left Panel & Right Panel
        self.left_panel = tk.Frame(root)
        self.left_panel.pack(side=tk.LEFT, padx=10, pady=10)

        self.right_panel = tk.Frame(root)
        self.right_panel.pack(side=tk.RIGHT, padx=10, pady=10)

        # Left Panel: Search Bar & Video List Toggle
        self.entry_search = tk.Entry(self.left_panel, width=30)
        self.entry_search.pack(pady=5)

        self.btn_search = tk.Button(self.left_panel, text="🔍 Search", command=self.search_video)
        self.btn_search.pack(pady=5)

        self.btn_show_list = tk.Button(self.left_panel, text="📋 Toggle Video List", command=self.toggle_video_list)
        self.btn_show_list.pack(pady=5)

        self.listbox_videos = tk.Listbox(self.left_panel, width=40, height=15)
        self.listbox_videos.pack(pady=10)
        self.listbox_videos.bind("<Double-Button-1>", self.on_video_select)

        self.btn_add_video = tk.Button(self.left_panel, text="➕ Add Video", command=self.add_video)
        self.btn_add_video.pack(pady=5)

        # Right Panel: Video Player & Controls
        self.video_frame = tk.Frame(self.right_panel, width=1080, height=490, bg="black")
        self.video_frame.pack(pady=10)

        self.seek_var = tk.DoubleVar()
        self.seek_bar = tk.Scale(self.right_panel, from_=0, to=100, orient=tk.HORIZONTAL, length=800,
                                 variable=self.seek_var, command=self.seek_video)
        self.seek_bar.pack()

        self.button_frame = tk.Frame(self.right_panel)
        self.button_frame.pack(pady=10)

        self.btn_play = tk.Button(self.button_frame, text="▶ Play", command=self.play_video, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=5)

        self.btn_pause = tk.Button(self.button_frame, text="⏸ Pause", command=self.pause_video, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(self.button_frame, text="⏹ Stop", command=self.stop_video, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_back = tk.Button(self.button_frame, text="🔙 Back", command=self.back_to_menu, state=tk.DISABLED)
        self.btn_back.pack(side=tk.LEFT, padx=5)

        self.audio_control_frame = tk.Frame(self.right_panel)
        self.audio_control_frame.pack(pady=10)

        self.btn_mute = tk.Button(self.audio_control_frame, text="🔊 Mute", command=self.toggle_mute)
        self.btn_mute.pack(side=tk.LEFT, padx=10)

        self.volume_slider = tk.Scale(self.audio_control_frame, from_=0, to=100, orient=tk.HORIZONTAL, label="🔈 Volume",
                                      command=self.set_volume)
        self.volume_slider.pack(side=tk.LEFT, padx=10)
        self.volume_slider.set(100)

        self.load_video_list()

    def load_video_list(self):
        self.listbox_videos.delete(0, tk.END)
        self.video_list = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith((".mp4", ".avi", ".mov", ".mkv"))]

        for video in self.video_list:
            self.listbox_videos.insert(tk.END, video)

    def search_video(self):
        query = self.entry_search.get().strip().lower()
        if not query:
            messagebox.showwarning("Warning", "Enter a video name to search")
            return

        matches = [v for v in self.video_list if query in v.lower()]

        self.listbox_videos.delete(0, tk.END)
        for video in matches:
            self.listbox_videos.insert(tk.END, video)

    def toggle_video_list(self):
        if self.video_list_visible:
            self.listbox_videos.pack_forget()
            self.btn_add_video.pack_forget()
        else:
            self.listbox_videos.pack(pady=10)
            self.btn_add_video.pack(pady=5)
        self.video_list_visible = not self.video_list_visible

    def on_video_select(self, event):
        selection = self.listbox_videos.curselection()
        if selection:
            self.video_path = os.path.join(VIDEO_FOLDER, self.listbox_videos.get(selection[0]))
            self.btn_play.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.NORMAL)

    def play_video(self):
        if not self.video_path:
            return

        if self.is_paused:
            self.media_player.play()
            self.is_paused = False
        else:
            media = self.instance.media_new(self.video_path)
            self.media_player.set_media(media)

            if os.name == "nt":
                self.media_player.set_hwnd(self.video_frame.winfo_id())
            else:
                self.media_player.set_xwindow(self.video_frame.winfo_id())

            self.media_player.play()

        self.btn_stop.config(state=tk.NORMAL)
        self.btn_back.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.NORMAL)

        threading.Thread(target=self.update_seek_bar, daemon=True).start()

    def pause_video(self):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.is_paused = True
            self.btn_pause.config(text="▶ Resume")
        else:
            self.media_player.play()
            self.is_paused = False
            self.btn_pause.config(text="⏸ Pause")

    def stop_video(self):
        self.media_player.stop()
        self.is_paused = False
        self.btn_pause.config(text="⏸ Pause", state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)

    def back_to_menu(self):
        self.stop_video()
        self.btn_back.config(state=tk.DISABLED)

    def add_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv")])
        if file_path:
            file_name = os.path.basename(file_path)
            new_path = os.path.join(VIDEO_FOLDER, file_name)
            if not os.path.exists(new_path):
                os.rename(file_path, new_path)
                self.load_video_list()
            else:
                messagebox.showerror("Error", "Video already exists in the folder")

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.media_player.audio_toggle_mute()
        self.btn_mute.config(text="🔇 Unmute" if self.is_muted else "🔊 Mute")

    def set_volume(self, volume):
        self.media_player.audio_set_volume(int(volume))

    def seek_video(self, position):
        if self.media_player.get_length() > 0:
            new_time = int((self.media_player.get_length() * float(position)) / 100)
            self.media_player.set_time(new_time)

    def update_seek_bar(self):
        while self.media_player.get_state() not in [vlc.State.Ended, vlc.State.Stopped]:
            if not self.is_seeking:
                length = self.media_player.get_length()
                if length > 0:
                    current_time = self.media_player.get_time()
                    position = (current_time / length) * 100
                    self.seek_var.set(position)
            time.sleep(0.5)


root = tk.Tk()
app = VideoPlayer(root)
root.mainloop()
