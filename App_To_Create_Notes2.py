import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import pyaudio
import wave
from vosk import Model, KaldiRecognizer
from fpdf import FPDF


class MeetingRecorderApp:
    def __init__(self):
        self.audio_filename = "audio_recording.wav"
        self.is_recording = False
        self.transcription = ""
        self.audio_thread = None
        self.transcription_thread = None
        self.stream = None
        self.p = None
        self.recognizer = None

        # Model path for Vosk
        self.model_path = "./vosk-model-small-pl-0.22"  # Ensure to download and extract this model

    def start_audio_recording(self):
        if self.is_recording:
            messagebox.showinfo("Nagrywanie", "Nagrywanie już trwa!")
            return

        self.is_recording = True
        self.transcription = ""
        self.audio_thread = threading.Thread(target=self.record_and_transcribe)
        self.audio_thread.start()
        messagebox.showinfo("Nagrywanie", "Nagrywanie i transkrypcja rozpoczęte!")

    def record_and_transcribe(self):
        try:
            # Inicjalizacja nagrywania
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=16000,
                                      input=True,
                                      frames_per_buffer=1024)
            frames = []

            # Inicjalizacja modelu Vosk
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model nie znaleziony w {self.model_path}. Pobierz go z https://alphacephei.com/vosk/models.")
            model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(model, 16000)

            # Nagrywanie i transkrypcja w czasie rzeczywistym
            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                frames.append(data)
                if self.recognizer.AcceptWaveform(data):
                    result = self.recognizer.Result()
                    self.transcription += result

            # Zapis nagrania do pliku audio
            with wave.open(self.audio_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się nagrać lub przetranskrybować: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()

    def stop_audio_recording(self):
        if not self.is_recording:
            messagebox.showinfo("Nagrywanie", "Nagrywanie nie jest aktywne!")
            return

        self.is_recording = False

        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()

        messagebox.showinfo("Nagrywanie", f"Nagrywanie zakończone. Plik zapisany jako {self.audio_filename}")

    def save_notes(self):
        if not self.transcription.strip():
            messagebox.showinfo("Zapis", "Brak notatek do zapisania!")
            return

        # Wyświetl okno dialogowe z wyborem formatu
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

        # Okno dialogowe wyboru formatu
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

        # Update transcription text in real-time
        def update_transcription_text():
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.END, self.transcription)
            root.after(1000, update_transcription_text)

        update_transcription_text()
        root.mainloop()


if __name__ == "__main__":
    app = MeetingRecorderApp()
    app.start_ui()
