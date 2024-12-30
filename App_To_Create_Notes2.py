import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
import json
import numpy as np
import soundcard as sc
import soundfile as sf
from vosk import Model, KaldiRecognizer
from fpdf import FPDF
from datetime import datetime
from pydub import AudioSegment
from pydub.utils import which
from pydub import AudioSegment

AudioSegment.converter = which("ffmpeg")


class MeetingRecorderApp:
    def __init__(self):
        self.audio_filename = ""
        self.is_recording = False
        self.transcription = ""
        self.model_path = "./vosk-model-small-pl-0.22"
        self.samplerate = 48000
        self.blocksize = 2048
        self.recorder = None

        # Folder na nagrania
        self.recordings_folder = "./recordings"
        if not os.path.exists(self.recordings_folder):
            os.makedirs(self.recordings_folder)

        # Domyślny format nagrań
        self.audio_format = "wav"

    def start_audio_recording(self):
        if self.is_recording:
            messagebox.showinfo("Recording", "Recording is already in progress!")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.audio_filename = os.path.join(self.recordings_folder, f"{timestamp}.{self.audio_format}")

        self.is_recording = True
        self.transcription = ""
        threading.Thread(target=self.record_and_transcribe).start()
        messagebox.showinfo("Recording", "Recording and transcription started!")

    def record_and_transcribe(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError("Vosk model not found.")
            model = Model(self.model_path)
            recognizer = KaldiRecognizer(model, self.samplerate)

            with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(
                    samplerate=self.samplerate, blocksize=self.blocksize) as mic:
                frames = []
                while self.is_recording:
                    data = mic.record(numframes=self.blocksize)
                    data_mono = np.mean(data, axis=1) if data.ndim > 1 else data
                    data_int16 = (data_mono * 32767).astype(np.int16)
                    frames.append(data_int16)

                    if recognizer.AcceptWaveform(data_int16.tobytes()):
                        parsed_result = json.loads(recognizer.Result())
                        if "text" in parsed_result:
                            self.transcription += parsed_result["text"] + "\n"

                audio_data = np.concatenate(frames, axis=0)
                sf.write(self.audio_filename, audio_data, samplerate=self.samplerate)

                if self.audio_format == "mp3":
                    wav_audio = AudioSegment.from_wav(self.audio_filename)
                    self.audio_filename = self.audio_filename.replace(".wav", ".mp3")
                    wav_audio.export(self.audio_filename, format="mp3")
                    os.remove(self.audio_filename.replace(".mp3", ".wav"))

        except Exception:
            pass
        finally:
            self.is_recording = False

    def stop_audio_recording(self):
        if not self.is_recording:
            messagebox.showinfo("Recording", "No active recording to stop!")
            return

        self.is_recording = False
        messagebox.showinfo("Recording", f"Recording stopped. File saved as {self.audio_filename}")

    def save_notes(self):
        if not self.transcription.strip():
            messagebox.showinfo("Save Notes", "No transcription available to save!")
            return

        def save_as(format):
            if format == "TXT":
                txt_filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                            filetypes=[("Text files", "*.txt")])
                if txt_filename:
                    with open(txt_filename, "w", encoding="utf-8") as f:
                        f.write(self.transcription)
                    messagebox.showinfo("Save Notes", f"Notes saved as {txt_filename}")
            elif format == "PDF":
                pdf_filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                            filetypes=[("PDF files", "*.pdf")])
                if pdf_filename:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    for line in self.transcription.split("\n"):
                        pdf.multi_cell(0, 10, line)
                    pdf.output(pdf_filename)
                    messagebox.showinfo("Save Notes", f"Notes saved as {pdf_filename}")
            save_window.destroy()

        save_window = tk.Toplevel()
        save_window.title("Choose Save Format")
        ttk.Label(save_window, text="Select format to save notes:").pack(pady=10)
        ttk.Button(save_window, text="Save as TXT", command=lambda: save_as("TXT")).pack(pady=5)
        ttk.Button(save_window, text="Save as PDF", command=lambda: save_as("PDF")).pack(pady=5)

    def browse_recordings(self):
        folder_path = os.path.abspath(self.recordings_folder)
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            messagebox.showerror("Error", f"Folder {folder_path} does not exist!")

    def open_settings(self):
        if self.is_recording:
            messagebox.showinfo("Settings", "Stop the recording before opening settings!")
            return

        settings_window = tk.Toplevel()
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        ttk.Label(settings_window, text="Choose Language:").pack(pady=10)

        language_var = tk.StringVar(value="Polski")

        ttk.Radiobutton(settings_window, text="Polski", variable=language_var, value="Polski").pack(anchor=tk.W)
        ttk.Radiobutton(settings_window, text="English", variable=language_var, value="English").pack(anchor=tk.W)

        ttk.Label(settings_window, text="Choose Recording Format:").pack(pady=10)

        format_var = tk.StringVar(value=self.audio_format)

        ttk.Radiobutton(settings_window, text="WAV", variable=format_var, value="wav").pack(anchor=tk.W)
        ttk.Radiobutton(settings_window, text="MP3", variable=format_var, value="mp3").pack(anchor=tk.W)

        def save_settings():
            self.audio_format = format_var.get()
            messagebox.showinfo("Settings", "Settings saved.")
            settings_window.destroy()

        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)

    def start_ui(self):
        root = tk.Tk()
        root.title("Meeting Recorder")
        root.geometry("900x650")
        style = ttk.Style()
        style.configure("TButton", padding=5, relief="flat", font=("Helvetica", 12))
        style.configure("TLabel", font=("Helvetica", 12))

        header = ttk.Label(root, text="Meeting Recorder Application", font=("Helvetica", 18, "bold"))
        header.pack(pady=20)

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="🎙 Start Recording", command=self.start_audio_recording).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="⏹ Stop Recording", command=self.stop_audio_recording).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="💾 Save Notes", command=self.save_notes).grid(row=0, column=2, padx=10)
        ttk.Button(button_frame, text="📂 Browse Recordings", command=self.browse_recordings).grid(row=0, column=3, padx=10)
        ttk.Button(button_frame, text="⚙️ Settings", command=self.open_settings).grid(row=0, column=4, padx=10)

        transcription_label = ttk.Label(root, text="Transcription:", font=("Helvetica", 14))
        transcription_label.pack(pady=10)

        transcription_frame = ttk.Frame(root, borderwidth=2, relief="groove")
        transcription_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.transcription_text = ScrolledText(transcription_frame, wrap=tk.WORD, width=80, height=20)
        self.transcription_text.pack(padx=10, pady=10, fill="both", expand=True)

        def update_transcription_text():
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.END, self.transcription)
            root.after(1000, update_transcription_text)

        update_transcription_text()
        root.mainloop()


if __name__ == "__main__":
    app = MeetingRecorderApp()
    app.start_ui()
