import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import json
import numpy as np
import soundcard as sc
import soundfile as sf
from vosk import Model, KaldiRecognizer
from fpdf import FPDF


class MeetingRecorderApp:
    def __init__(self):
        self.audio_filename = "audio_recording.wav"
        self.is_recording = False
        self.transcription = ""
        self.model_path = "./vosk-model-small-pl-0.22"
        self.samplerate = 48000
        self.blocksize = 2048  # Zwiększony rozmiar bufora
        self.recorder = None

    def start_audio_recording(self):
        if self.is_recording:
            messagebox.showinfo("Nagrywanie", "Nagrywanie już trwa!")
            return

        self.is_recording = True
        self.transcription = ""
        threading.Thread(target=self.record_and_transcribe).start()
        messagebox.showinfo("Nagrywanie", "Nagrywanie i transkrypcja rozpoczęte!")

    def record_and_transcribe(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError("Nie znaleziono modelu Vosk.")
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
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się nagrać lub przetranskrybować: {e}")
        finally:
            self.is_recording = False

    def stop_audio_recording(self):
        if not self.is_recording:
            messagebox.showinfo("Nagrywanie", "Nagrywanie nie jest aktywne!")
            return

        self.is_recording = False
        messagebox.showinfo("Nagrywanie", f"Nagrywanie zakończone. Plik zapisany jako {self.audio_filename}")

    def save_notes(self):
        if not self.transcription.strip():
            messagebox.showinfo("Zapis", "Brak notatek do zapisania!")
            return

        def save_as(format):
            if format == "TXT":
                txt_filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                            filetypes=[("Text files", "*.txt")])
                if txt_filename:
                    with open(txt_filename, "w", encoding="utf-8") as f:
                        f.write(self.transcription)
                    messagebox.showinfo("Zapis", f"Notatki zapisane jako {txt_filename}")
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
                    messagebox.showinfo("Zapis", f"Notatki zapisane jako {pdf_filename}")
            save_window.destroy()

        save_window = tk.Toplevel()
        save_window.title("Wybierz format zapisu")
        tk.Label(save_window, text="Wybierz format zapisu notatek:").pack(pady=10)
        tk.Button(save_window, text="Zapisz jako TXT", command=lambda: save_as("TXT")).pack(pady=5)
        tk.Button(save_window, text="Zapisz jako PDF", command=lambda: save_as("PDF")).pack(pady=5)

    def start_ui(self):
        root = tk.Tk()
        root.title("Meeting Recorder")

        tk.Label(root, text="Meeting Recorder Application").pack(pady=10)
        tk.Button(root, text="Start Recording", command=self.start_audio_recording).pack(pady=5)
        tk.Button(root, text="Stop Recording", command=self.stop_audio_recording).pack(pady=5)
        tk.Button(root, text="Save Notes", command=self.save_notes).pack(pady=5)

        self.transcription_text = ScrolledText(root, wrap=tk.WORD, width=80, height=20)
        self.transcription_text.pack(padx=10, pady=10)

        def update_transcription_text():
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.END, self.transcription)
            root.after(1000, update_transcription_text)

        update_transcription_text()
        root.mainloop()


if __name__ == "__main__":
    app = MeetingRecorderApp()
    app.start_ui()
