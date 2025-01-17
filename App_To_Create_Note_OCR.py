import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import pyaudio
import wave
from vosk import Model, KaldiRecognizer
from fpdf import FPDF
import pyautogui
import pytesseract
from datetime import datetime
import hashlib


class MeetingRecorderApp:
    def __init__(self):
        self.audio_filename = "audio_recording.wav"
        self.is_recording = False
        self.transcription = ""
        self.audio_thread = None
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.transcription_file = "transcription.txt"
        self.model_path = "./vosk-model-small-pl-0.22"  # Path to Vosk model
        self.screenshot_interval = 10  # Interval for taking screenshots (in seconds)

        # Określenie ścieżki do Tesseract (ręczne ustawienie)
        pytesseract.pytesseract.tesseract_cmd = r'E:\Tesseract\tesseract.exe'  # Wskaż właściwą ścieżkę do tesseract.exe

        # Przechowywanie haseł hash z poprzednich zrzutów ekranu i rozpoznanych tekstów
        self.previous_screenshot_hashes = set()
        self.previous_texts = set()

    def start_audio_recording(self):
        if self.is_recording:
            messagebox.showinfo("Nagrywanie", "Nagrywanie już trwa!")
            return

        self.is_recording = True
        self.transcription = ""
        self.audio_thread = threading.Thread(target=self.record_and_transcribe)
        self.audio_thread.start()
        self.screenshot_thread = threading.Thread(target=self.capture_screenshots)
        self.screenshot_thread.start()
        messagebox.showinfo("Nagrywanie", "Nagrywanie i transkrypcja rozpoczęte!")

    def record_and_transcribe(self):
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=16000,
                                      input=True,
                                      frames_per_buffer=1024)
            frames = []

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"Model nie znaleziony w {self.model_path}. Pobierz go z https://alphacephei.com/vosk/models.")
            model = Model(self.model_path)
            recognizer = KaldiRecognizer(model, 16000)

            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                frames.append(data)
                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    self.transcription += result

            with wave.open(self.audio_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()

    def capture_screenshots(self):
        while self.is_recording:
            screenshot_path = self.take_screenshot()
            self.perform_ocr(screenshot_path)
            threading.Event().wait(self.screenshot_interval)

    def take_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        return screenshot_path

    def perform_ocr(self, image_path):
        try:
            # Wykonaj OCR na obrazie
            text = pytesseract.image_to_string(image_path, lang="eng")

            # Generowanie hasha z obrazu (żeby porównać z poprzednimi)
            screenshot_hash = self.get_image_hash(image_path)

            # Jeśli obrazek jest już przetworzony, nie robimy OCR
            if screenshot_hash in self.previous_screenshot_hashes:
                print(f"Screenshot {image_path} already processed, skipping OCR.")
                return

            # Jeśli tekst został już rozpoznany wcześniej, nie dodajemy go ponownie
            if text.strip() and text.strip() not in self.previous_texts:
                self.transcription += f"\n[OCR: {text.strip()}]\n"
                self.previous_texts.add(text.strip())

            # Dodajemy hash obrazu do zbioru, aby zapobiec ponownemu przetwarzaniu
            self.previous_screenshot_hashes.add(screenshot_hash)

        except Exception as e:
            print(f"Error performing OCR: {e}")

    def get_image_hash(self, image_path):
        """Generuje hash obrazu, aby porównać, czy obraz jest taki sam jak poprzedni."""
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return hashlib.md5(image_data).hexdigest()

    def stop_audio_recording(self):
        if not self.is_recording:
            messagebox.showinfo("Nagrywanie", "Nagrywanie nie jest aktywne!")
            return

        self.is_recording = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()
        if self.screenshot_thread and self.screenshot_thread.is_alive():
            self.screenshot_thread.join()

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
            current_pos = self.transcription_text.yview()[1]  # Pozycja suwaka
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.END, self.transcription)

            # Przewiń suwak, jeśli był blisko końca
            if current_pos > 0.9:  # Jeśli suwak jest blisko końca
                self.transcription_text.yview_moveto(1)  # Przewiń do końca
            root.after(1000, update_transcription_text)

        update_transcription_text()
        root.mainloop()


if __name__ == "__main__":
    app = MeetingRecorderApp()
    app.start_ui()
