#!/usr/bin/env /home/user/miniforge3/envs/mywhisper/bin/python3

import os
import pyperclip
import whisper
import pyaudio
import wave
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import webrtcvad
#sudo apt-get install libasound2-dev

def record_audio(filename="audio.wav"):
    """Record audio from the microphone and stop when silence is detected."""
    sample_rate = 16000  # 16000 samples per second
    frame_duration = 30  # Frame size in ms
    vad = webrtcvad.Vad(1)  # Set aggressiveness mode (0-3)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=int(sample_rate * frame_duration / 1000))

    frames = []
    silence_threshold = 30  # Number of consecutive silent frames to stop
    silent_frames = 0

    try:
        while True:
            frame = stream.read(int(sample_rate * frame_duration / 1000))
            frames.append(frame)
            is_speech = vad.is_speech(frame, sample_rate)
            if not is_speech:
                silent_frames += 1
                if silent_frames > silence_threshold:
                    break
            else:
                silent_frames = 0
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("My Whispers")
        self.root.geometry("400x250")
        self.root.attributes('-topmost', True)

        # Apply GNOME-like theme
        style = ttk.Style()
        style.theme_use('clam')  # Use 'clam' as a base theme

        # Set background colors
        style.configure('.', background='#333333')
        root.configure(background='#333333')

        # Configure Labels
        style.configure('TLabel',
                        background='#f0f0f0',
                        foreground='#333333',
                        font=('Sans', 10))

        # Configure Buttons
        style.configure('TButton',
                        background='#28a745',
                        foreground='white',
                        font=('Sans', 10),
                        padding=6)
        style.map('TButton',
                  background=[('active', '#218838'), ('disabled', '#a9a9a9')],
                  foreground=[('disabled', '#ffffff')])

        # Status Label
        self.status_label = ttk.Label(root, text="Idle")
        self.status_label.pack(pady=5)
        self.status_label.configure(background='#333333', foreground='#f0f0f0')

        # Text Area
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=8,
                                                   font=('Sans', 10), background='#ffffff',
                                                   foreground='#000000', borderwidth=0)
        self.text_area.pack(padx=10, pady=5)

        # Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5)

        # Left Frame for Start Button
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side=tk.LEFT, padx=5)

        # Start Recording Button
        self.record_button = ttk.Button(left_frame, text="Start Recording", command=self.start_recording)
        self.record_button.pack()

        # Right Frame for Stop Button
        right_frame = ttk.Frame(button_frame)
        right_frame.pack(side=tk.RIGHT, padx=5)

        # Stop Recording Button
        self.stop_button = ttk.Button(right_frame, text="Stop Recording", command=self.stop_recording)
        self.stop_button.pack()

        # Copy Button below in middle
        self.copy_button = ttk.Button(self.root, text="Copy to Clipboard", command=self.copy_text, state=tk.DISABLED)
        self.copy_button.pack(pady=5)

        # Define available Whisper models
        self.available_models = ["tiny", "base", "small", "medium", "large", "turbo"]
        self.selected_model = tk.StringVar(value="base")  # Default model

        # Create menu bar
        menu_bar = tk.Menu(self.root)
        menu_bar.configure(background='#333333', foreground='#f0f0f0')
        self.root.config(menu=menu_bar)

        # Create Model menu
        model_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Model", menu=model_menu)

        # Add model options to Model menu
        for model in self.available_models:
            model_menu.add_radiobutton(label=model.capitalize(), variable=self.selected_model, command=self.on_model_change)

        # Define a BooleanVar for Always on Top
        self.always_on_top = tk.BooleanVar(value=False)

        # Create Options menu
        options_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Options", menu=options_menu)

        # Add Always on Top checkbutton to Options menu
        options_menu.add_checkbutton(label="Always on Top",
                                     variable=self.always_on_top,
                                     command=self.toggle_always_on_top)

        # Load Whisper model in a thread
        threading.Thread(target=self.load_model).start()

    def on_model_change(self):
        self.update_status(f"Loading {self.selected_model.get()} model...")
        threading.Thread(target=self.load_model).start()

    def load_model(self):
        self.model = whisper.load_model(self.selected_model.get().lower())
        self.update_status(f"{self.selected_model.get().capitalize()} model loaded.")

    def update_status(self, status):
        self.status_label.config(text=status)

    def display_text(self, text):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)

    def copy_text(self):
        text = self.text_area.get("1.0", tk.END).strip()
        pyperclip.copy(text)
        self.update_status("Text copied to clipboard.")

    def auto_copy(self):
        text = self.text_area.get("1.0", tk.END).strip()
        pyperclip.copy(text)
        self.update_status("Text copied to clipboard.")

    def start_recording(self):
        self.record_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)
        threading.Thread(target=self.process).start()

    def stop_recording(self):
        # Implement logic to stop recording
        pass  # Replace with actual code to stop recording

    def process(self):
        temp_audio_path = "audio.wav"
        self.update_status("Recording...")
        record_audio(filename=temp_audio_path)
        self.update_status("Recording complete.")
        self.transcribe_audio(temp_audio_path)
        os.remove(temp_audio_path)
        self.record_button.config(state=tk.NORMAL)

    def transcribe_audio(self, audio_path):
        self.update_status("Transcribing audio...")
        result = self.model.transcribe(audio_path)
        text = result['text'].strip()
        self.display_text(text)
        self.update_status("Transcription complete.")
        self.auto_copy()
        self.copy_button.config(state=tk.NORMAL)

    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.always_on_top.get())

def main():
    root = tk.Tk()
    gui = AppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
