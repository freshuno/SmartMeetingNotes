import os
import wave
import threading
import queue
import pyaudio
from vosk import Model, KaldiRecognizer
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import ImageGrab
from datetime import datetime
import pyautogui
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplikacja do Notatek")
        self.geometry("800x600")
        self.transcription_text = None
        self.transcription_content = ""  # Przechowujemy transkrypcję

        # UI
        self.create_ui()

    def create_ui(self):
        tk.Button(self, text="Start Nagrywanie", command=self.start_recording).pack(pady=10)
        tk.Button(self, text="Stop Nagrywanie", command=self.stop_recording).pack(pady=10)
        tk.Button(self, text="Zrób Zrzut Ekranu", command=self.capture_screen).pack(pady=10)
        tk.Button(self, text="Zapisz jako TXT", command=self.save_as_txt).pack(pady=10)
        tk.Button(self, text="Zapisz jako PDF", command=self.save_as_pdf).pack(pady=10)
        self.transcription_text = ScrolledText(self, wrap=tk.WORD, width=80, height=25)
        self.transcription_text.pack(padx=10, pady=10)

    def start_recording(self):
        # Tworzenie kolejki i zdarzenia do zatrzymania nagrywania
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()  # Użycie zdarzenia do kontrolowania zakończenia
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.transcription_thread = threading.Thread(target=self.transcribe_live_audio)
        self.recording_thread.start()
        self.transcription_thread.start()
        self.transcription_text.insert(tk.END, "Nagrywanie rozpoczęte...\n")

    def stop_recording(self):
        # Ustawia sygnał zatrzymania
        self.stop_event.set()

        # Czekaj, aż wątki się zakończą
        self.recording_thread.join()
        self.transcription_thread.join()

        self.transcription_text.insert(tk.END, "Nagrywanie zakończone.\n")
        messagebox.showinfo("Nagrywanie zakończone", "Nagrywanie zostało zatrzymane.")

    def record_audio(self):
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            frames_per_buffer=4000)
            while not self.stop_event.is_set():
                data = stream.read(4000, exception_on_overflow=False)
                self.audio_queue.put(data)

            # Zatrzymanie streamu i zwolnienie zasobów
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            self.transcription_text.insert(tk.END, f"Error in recording: {e}\n")

    def transcribe_live_audio(self):
        try:
            model_path = "./vosk-model-small-pl-0.22"
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Model językowy nie znaleziony w {model_path}. Pobierz model z https://alphacephei.com/vosk/models i wypakuj go tutaj.")

            model = Model(model_path)
            recognizer = KaldiRecognizer(model, 16000)

            while not self.stop_event.is_set():
                try:
                    data = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    continue

                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    self.transcription_text.insert(tk.END, result + "\n")
                    self.transcription_content += result + "\n"  # Zapisanie wyniku do zmiennej

            # Dodanie końcowego wyniku
            final_result = recognizer.FinalResult()
            self.transcription_text.insert(tk.END, final_result + "\n")
            self.transcription_content += final_result + "\n"
        except Exception as e:
            self.transcription_text.insert(tk.END, f"Error in transcription: {e}\n")

    def capture_screen(self):
        try:
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(filename)
            messagebox.showinfo("Zrzut ekranu", f"Zrzut ekranu zapisano jako {filename}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać zrzutu ekranu: {e}")

    def save_as_txt(self):
        try:
            if not self.transcription_content:
                messagebox.showwarning("Brak danych", "Brak dostępnych danych do zapisania.")
                return

            file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                     filetypes=[("Text files", "*.txt")],
                                                     title="Zapisz jako TXT")
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(self.transcription_content)
                messagebox.showinfo("Zapisano", f"Notatki zostały zapisane jako {file_path}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku TXT: {e}")

    def save_as_pdf(self):
        try:
            if not self.transcription_content:
                messagebox.showwarning("Brak danych", "Brak dostępnych danych do zapisania.")
                return

            file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                     filetypes=[("PDF files", "*.pdf")],
                                                     title="Zapisz jako PDF")
            if file_path:
                c = canvas.Canvas(file_path, pagesize=letter)
                text_object = c.beginText(40, 750)
                text_object.setFont("Helvetica", 10)
                text_object.setTextOrigin(40, 750)

                # Dodaj tekst transkrypcji do PDF
                lines = self.transcription_content.splitlines()
                for line in lines:
                    text_object.textLine(line)

                c.drawText(text_object)
                c.showPage()
                c.save()
                messagebox.showinfo("Zapisano", f"Notatki zostały zapisane jako {file_path}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku PDF: {e}")


# Uruchomienie aplikacji
if __name__ == "__main__":
    app = NotesApp()
    app.mainloop()
