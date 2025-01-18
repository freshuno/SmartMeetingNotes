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
import openai
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
AudioSegment.converter = which("ffmpeg")
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
import textwrap
from tkinter import messagebox, filedialog
import time
import fitz

# Pobierz potrzebne dane NLTK (raz)
#nltk.download("punkt")
#nltk.download("punkt_tab")

# Załaduj model języka polskiego (Spacy)
nlp = spacy.load("pl_core_news_sm")

# Polskie stop words
polish_stop_words = [
    "i", "oraz", "a", "ale", "lub", "więc", "z", "na", "że", "czy", "jak",
    "tak", "jest", "by", "co", "tego", "dla", "to", "od", "do", "po", "przez",
    "nie", "jego", "jej", "się", "o", "ze", "u", "za", "bez", "w", "który",
    "która", "które", "kto", "kogo", "gdzie", "czyli", "tam", "tu", "nad",
    "pod", "jakie", "jaki", "taki", "ta", "ten", "te"
]

def lemmatize_text(text):
    doc = nlp(text)
    lemmatized_sentences = [" ".join([token.lemma_ for token in sent]) for sent in doc.sents]
    return " ".join(lemmatized_sentences)

def summarize_with_ai(text, api_key, num_sentences=3):
    """
    Podsumowywanie tekstu za pomocą Cohere AI.
    """
    import cohere

    co = cohere.Client("9UFiMQMILWQRjprgjeVztTywY6si7xF0RjTT8IYC")

    # Tworzymy prompt dla Cohere
    document = text.strip()
    prompt = f"Summarize the following text in {num_sentences} sentences: {document}"

    try:
        response = co.generate(
            model="command-r-plus-08-2024",
            prompt=prompt,
            max_tokens=500
        )
        summary = response.generations[0].text.strip()
        return summary
    except Exception as e:
        return f"An error occurred while generating the summary: {e}"

class MeetingRecorderApp:
    def __init__(self):
        # Inicjalizacja elementów aplikacji (bez zmian funkcjonalnych)
        self.root = None
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

        self.audio_format = "wav"

    def start_ui(self):
        self.root = ttk.Window(themename="flatly")
        root = self.root
        root = ttk.Window(themename="flatly")
        root.title("Meeting Recorder")
        root.geometry("900x700")

        # Nagłówek aplikacji
        header_frame = ttk.Frame(root, padding=10)
        header_frame.pack(fill=X)
        header_label = ttk.Label(
            header_frame, text="Meeting Recorder Application", font=("Helvetica", 20, "bold"), anchor=CENTER
        )
        header_label.pack(fill=X)

        # Obszar transkrypcji
        transcription_label = ttk.Label(
            root, text="Transcription:", font=("Helvetica", 14), anchor=W
        )
        transcription_label.pack(fill=X, padx=10, pady=5)

        transcription_frame = ttk.Frame(root, padding=10, relief=RIDGE)
        transcription_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.transcription_text = ttk.ScrolledText(
            transcription_frame, wrap=WORD, height=20, width=80, font=("Helvetica", 12)
        )
        self.transcription_text.pack(fill=BOTH, expand=True)

        # Aktualizacja transkrypcji w czasie rzeczywistym
        def update_transcription_text():
            self.transcription_text.delete(1.0, END)
            self.transcription_text.insert(END, self.transcription)
            root.after(1000, update_transcription_text)

        update_transcription_text()
        root.mainloop()

    # Pozostałe funkcje aplikacji (zachowane bez zmian)
    def start_audio_recording(self):
        pass

    def stop_audio_recording(self):
        pass

    def save_notes(self):
        pass

    def summarize_notes(self):
        pass

    def browse_notes(self):
        pass

    def browse_recordings(self):
        pass

    def open_settings(self):
        pass

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
            messagebox.showwarning("Warning", "No transcription to save.")
            return

        # Ścieżka do folderu, gdzie będą zapisywane notatki
        notes_folder = "./notes"

        # Tworzymy folder, jeśli nie istnieje
        if not os.path.exists(notes_folder):
            os.makedirs(notes_folder)

        # Tworzenie okna z wyborem formatu
        def choose_format():
            format_window = tk.Toplevel()  # Tworzymy nowe okno
            format_window.title("Choose Format")

            # Zmienna do przechowywania wybranego formatu
            selected_format = tk.StringVar(value="txt")

            # Ustawienia dla radia Buttonów
            txt_radio = ttk.Radiobutton(format_window, text="TXT", value="txt", variable=selected_format)
            pdf_radio = ttk.Radiobutton(format_window, text="PDF", value="pdf", variable=selected_format)

            txt_radio.pack(pady=10)
            pdf_radio.pack(pady=10)

            def save_and_close():
                file_type = selected_format.get()
                format_window.destroy()
                self.save_file(file_type)

            # Przycisk do zapisania i zamknięcia okna
            save_button = ttk.Button(format_window, text="Save", command=save_and_close)
            save_button.pack(pady=20)

            format_window.mainloop()

        # Wywołanie okna wyboru formatu
        choose_format()

    def display_summary(self, summary, text_type):
        """Wyświetla podsumowanie w nowym oknie i dodaje opcję zapisu."""
        summary_window = tk.Toplevel()
        summary_window.title(text_type)
        summary_window.geometry("800x600")

        ttk.Label(summary_window, text=text_type, font=("Helvetica", 14)).pack(pady=10)

        summary_text = ScrolledText(summary_window, wrap=tk.WORD, width=80, height=20)
        summary_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        summary_text.insert(tk.END, summary)
        summary_text.configure(state="disabled")

        # Funkcja zapisu podsumowania
        def save_summary():
            # Folder na podsumowania
            summaries_folder = "./summaries"
            if not os.path.exists(summaries_folder):
                os.makedirs(summaries_folder)

            # Wybór formatu
            def choose_format():
                format_window = tk.Toplevel(summary_window)
                format_window.title("Choose Format")
                selected_format = tk.StringVar(value="txt")

                ttk.Radiobutton(format_window, text="TXT", value="txt", variable=selected_format).pack(pady=10)
                ttk.Radiobutton(format_window, text="PDF", value="pdf", variable=selected_format).pack(pady=10)

                def save_and_close():
                    file_type = selected_format.get()
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"summary_{timestamp}.{file_type}"
                    save_path = os.path.join(summaries_folder, filename)

                    if file_type == "txt":
                        with open(save_path, "w", encoding="utf-8") as f:
                            f.write(summary)
                    elif file_type == "pdf":
                        pdf = canvas.Canvas(save_path, pagesize=letter)
                        pdfmetrics.registerFont(TTFont("DejaVuSans", "./DejaVuSans.ttf"))
                        pdf.setFont("DejaVuSans", 12)
                        y = 750
                        for line in textwrap.wrap(summary, width=80):
                            pdf.drawString(50, y, line)
                            y -= 15
                        pdf.save()

                    messagebox.showinfo("Success", f"Summary saved as {filename}")
                    format_window.destroy()

                ttk.Button(format_window, text="Save", command=save_and_close).pack(pady=20)

            choose_format()

        # Przyciski w oknie podsumowania
        save_button = ttk.Button(summary_window, text="Save Summary", command=save_summary)
        save_button.pack(pady=10)

    def save_file(self, file_type):
        # Tworzenie unikalnej nazwy pliku
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        notes_folder = "./notes"  # Ścieżka do folderu, w którym zapisujemy plik

        # Generowanie nazwy pliku w zależności od formatu
        if file_type == 'txt':
            save_path = os.path.join(notes_folder, f"notes_{timestamp}.txt")
        else:
            save_path = os.path.join(notes_folder, f"notes_{timestamp}.pdf")

        try:
            # Zapisz jako TXT
            if save_path.endswith(".txt"):
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(self.transcription)

            # Zapisz jako PDF
            if save_path.endswith(".pdf"):
                # Tworzenie PDF z ReportLab
                pdf = canvas.Canvas(save_path, pagesize=letter)

                # Dodanie czcionki DejaVu Sans (lub innej)
                pdfmetrics.registerFont(
                    TTFont('DejaVuSans', './DejaVuSans.ttf'))  # Skopiuj plik DejaVuSans.ttf do folderu projektu
                pdf.setFont("DejaVuSans", 12)

                # Wymiary strony (szerokość i wysokość)
                page_width, page_height = letter

                # Ustawienie początkowej pozycji na stronie
                y_position = page_height - 50  # Startowa pozycja (z góry)

                # Definicja marginesów
                left_margin = 50
                right_margin = 50
                max_line_length = page_width - left_margin - right_margin  # Obliczanie maksymalnej szerokości tekstu

                # Dzielimy tekst na linie w taki sposób, aby nie przekraczały szerokości strony
                lines = self.transcription.splitlines()

                # Rysowanie tekstu w PDF
                for line in lines:
                    # Zawijanie tekstu na słowach
                    wrapped_lines = textwrap.wrap(line, width=100)  # Określenie szerokości zawijania

                    # Używamy tego samego algorytmu, ale zapewniamy, że linie nie będą łamane w miejscach gdzie to zbędne
                    for wrapped_line in wrapped_lines:
                        # Sprawdzamy, czy linia nie przekracza szerokości strony
                        while pdf.stringWidth(wrapped_line, "DejaVuSans", 12) > max_line_length:
                            # Jeśli linia jest za szeroka, szukamy miejsca, aby ją rozbić na dwie części
                            for i in range(len(wrapped_line), 0, -1):
                                if pdf.stringWidth(wrapped_line[:i], "DejaVuSans", 12) <= max_line_length:
                                    break
                            first_part = wrapped_line[:i]
                            second_part = wrapped_line[i:].strip()

                            # Rysowanie pierwszej części linii
                            pdf.drawString(left_margin, y_position, first_part)
                            y_position -= 15  # Zmniejszamy pozycję na stronie
                            if y_position < 50:  # Jeśli kończy się miejsce na stronie, dodajemy nową stronę
                                pdf.showPage()
                                pdf.setFont("DejaVuSans", 12)
                                y_position = page_height - 50  # Resetujemy pozycję na początku strony
                            wrapped_line = second_part  # Reszta tekstu

                        # Rysowanie reszty tekstu
                        pdf.drawString(left_margin, y_position, wrapped_line)
                        y_position -= 15  # Zmniejszamy pozycję na stronie

                        # Sprawdzamy, czy musimy dodać nową stronę
                        if y_position < 50:
                            pdf.showPage()
                            pdf.setFont("DejaVuSans", 12)
                            y_position = page_height - 50

                # Zapisanie PDF
                pdf.save()

            messagebox.showinfo("Success", "Notes saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving notes: {e}")

    def summarize_notes(self):
        if not self.transcription.strip():
            messagebox.showwarning("Warning", "No transcription to summarize.")
            return

        # Funkcja wykonywana w tle
        def run_summary():
            # Tworzymy okno z komunikatem
            loading_window = tk.Toplevel()
            loading_window.title("Please Wait")
            loading_window.geometry("300x100")

            ttk.Label(loading_window, text="Generating summary...", font=("Helvetica", 12)).pack(pady=20)
            loading_window.transient(self.root)  # Ustawienie okna jako modalnego
            loading_window.grab_set()  # Zablokowanie interakcji z głównym oknem

            try:
                # Klucz API Cohere
                cohere_api_key = "9UFiMQMILWQRjprgjeVztTywY6si7xF0RjTT8IYC"

                # Wygenerowanie podsumowania
                summary = summarize_with_ai(self.transcription, cohere_api_key)

                # Wyświetlenie podsumowania w GUI
                self.display_summary(summary, "Summary")

            finally:
                loading_window.destroy()  # Zamknięcie okna komunikatu

        # Uruchomienie wątku
        threading.Thread(target=run_summary).start()

    def browse_notes(self):
        notes_window = tk.Toplevel()
        notes_window.title("Available Notes")
        notes_window.geometry("800x600")  # Powiększamy okno na szerokość

        ttk.Label(notes_window, text="Available Notes:", font=("Helvetica", 14)).pack(pady=10)

        # Listbox z dodatkowymi informacjami
        listbox_frame = ttk.Frame(notes_window)
        listbox_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        columns = ("Name", "Size (KB)", "Date")
        notes_list = ttk.Treeview(listbox_frame, columns=columns, show="headings", height=15)
        notes_list.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            notes_list.heading(col, text=col, anchor=tk.CENTER)

        # Dostosowanie szerokości kolumn
        notes_list.column("Name", anchor=tk.W, width=300)
        notes_list.column("Size (KB)", anchor=tk.E, width=100)
        notes_list.column("Date", anchor=tk.W, width=200)

        # Załadowanie notatek
        notes_folder = "./notes"
        if not os.path.exists(notes_folder):
            os.makedirs(notes_folder)

        def load_notes(sort_by="Name", reverse=False):
            for row in notes_list.get_children():
                notes_list.delete(row)

            notes = [f for f in os.listdir(notes_folder) if f.endswith(".txt") or f.endswith(".pdf")]

            notes_info = []
            for note in notes:
                filepath = os.path.join(notes_folder, note)
                file_info = os.stat(filepath)
                size_kb = round(file_info.st_size / 1024, 2)  # Rozmiar w KB
                last_modified = datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                notes_info.append((note, size_kb, last_modified))

            sort_index = {"Name": 0, "Size (KB)": 1, "Date": 2}[sort_by]
            notes_info.sort(key=lambda x: x[sort_index], reverse=reverse)

            for note in notes_info:
                notes_list.insert("", tk.END, values=note)

        # Początkowe załadowanie
        load_notes()

        # Sortowanie po kliknięciu kolumny
        sort_order = {"Name": False, "Size (KB)": False, "Date": False}

        def on_column_click(col):
            sort_order[col] = not sort_order[col]  # Przełączenie kolejności sortowania
            load_notes(sort_by=col, reverse=sort_order[col])

        for col in columns:
            notes_list.heading(col, text=col, command=lambda c=col: on_column_click(c))

        # Działania
        def open_note():
            selected = notes_list.selection()
            if not selected:
                messagebox.showerror("Error", "No note selected!")
                return
            filename = notes_list.item(selected[0], "values")[0]
            filepath = os.path.join(notes_folder, filename)

            # Otwieranie pliku tekstowego
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
            # Otwieranie pliku PDF
            elif filename.endswith(".pdf"):
                with fitz.open(filepath) as doc:
                    content = ""
                    for page in doc:
                        content += page.get_text("text")

            # Wyświetlanie zawartości notatki
            self.display_summary(content, "Note")

        def delete_note():
            selected = notes_list.selection()
            if not selected:
                messagebox.showerror("Error", "No note selected!")
                return
            filename = notes_list.item(selected[0], "values")[0]
            os.remove(os.path.join(notes_folder, filename))
            load_notes()
            messagebox.showinfo("Delete", f"{filename} deleted successfully!")

        def rename_note():
            selected = notes_list.selection()
            if not selected:
                messagebox.showerror("Error", "No note selected!")
                return
            old_filename = notes_list.item(selected[0], "values")[0]
            rename_window = tk.Toplevel(notes_window)
            rename_window.title("Rename Note")

            # Ustawienie minimalnego rozmiaru okna
            rename_window.minsize(300, 150)

            ttk.Label(rename_window, text="Enter new name (without extension):").pack(pady=10)
            new_name_var = tk.StringVar(value=os.path.splitext(old_filename)[0])
            new_name_entry = ttk.Entry(rename_window, textvariable=new_name_var)
            new_name_entry.pack(pady=5)

            # Konfiguracja okna, aby pojawiało się na środku ekranu
            rename_window.update_idletasks()  # Aktualizuje informacje o geometrii okna
            window_width = rename_window.winfo_width()
            window_height = rename_window.winfo_height()

            screen_width = rename_window.winfo_screenwidth()
            screen_height = rename_window.winfo_screenheight()

            position_x = (screen_width // 2) - (window_width // 2)
            position_y = (screen_height // 2) - (window_height // 2)

            rename_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

            def apply_rename():
                new_name = new_name_var.get().strip()
                if not new_name:
                    messagebox.showerror("Error", "Name cannot be empty!")
                    return
                new_filename = f"{new_name}{os.path.splitext(old_filename)[1]}"
                os.rename(
                    os.path.join(notes_folder, old_filename),
                    os.path.join(notes_folder, new_filename)
                )
                load_notes()
                rename_window.destroy()
                messagebox.showinfo("Rename", f"Renamed to {new_filename}")

            ttk.Button(rename_window, text="Rename", command=apply_rename).pack(pady=10)

        def summarize_selected_note():
            selected = notes_list.selection()
            if not selected:
                messagebox.showerror("Error", "No note selected!")
                return

            filename = notes_list.item(selected[0], "values")[0]
            filepath = os.path.join(notes_folder, filename)

            # Odczytanie zawartości notatki
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as file:
                    note_content = file.read()
            elif filename.endswith(".pdf"):
                with fitz.open(filepath) as doc:
                    note_content = ""
                    for page in doc:
                        note_content += page.get_text("text")

            # Podsumowanie notatki
            def run_summary():
                # Tworzymy okno z komunikatem
                loading_window = tk.Toplevel()
                loading_window.title("Please Wait")
                loading_window.geometry("300x100")
                ttk.Label(loading_window, text="Generating summary...", font=("Helvetica", 12)).pack(pady=20)
                loading_window.transient(notes_window)  # Modalne okno
                loading_window.grab_set()  # Blokada interakcji z głównym oknem

                try:
                    # Klucz API Cohere
                    cohere_api_key = "9UFiMQMILWQRjprgjeVztTywY6si7xF0RjTT8IYC"
                    summary = summarize_with_ai(note_content, cohere_api_key)
                    self.display_summary(summary, "Summary")

                finally:
                    loading_window.destroy()  # Zamknięcie okna komunikatu

            threading.Thread(target=run_summary).start()

        # Przyciski akcji
        button_frame = ttk.Frame(notes_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Open", command=open_note).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Delete", command=delete_note).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Rename", command=rename_note).grid(row=0, column=2, padx=10)
        ttk.Button(button_frame, text="Summarize Note", command=summarize_selected_note).grid(row=0, column=3, padx=10)

    def browse_summaries(self):
        summaries_window = tk.Toplevel()
        summaries_window.title("Available Summaries")
        summaries_window.geometry("800x600")

        ttk.Label(summaries_window, text="Available Summaries:", font=("Helvetica", 14)).pack(pady=10)

        # Frame for TreeView
        listbox_frame = ttk.Frame(summaries_window)
        listbox_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        columns = ("Name", "Size (KB)", "Date")
        summaries_list = ttk.Treeview(listbox_frame, columns=columns, show="headings", height=15)
        summaries_list.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            summaries_list.heading(col, text=col, anchor=tk.CENTER)

        # Column sizes
        summaries_list.column("Name", anchor=tk.W, width=300)
        summaries_list.column("Size (KB)", anchor=tk.E, width=100)
        summaries_list.column("Date", anchor=tk.W, width=200)

        # Load summaries
        summaries_folder = "./summaries"
        if not os.path.exists(summaries_folder):
            os.makedirs(summaries_folder)

        def load_summaries(sort_by="Name", reverse=False):
            for row in summaries_list.get_children():
                summaries_list.delete(row)

            summaries = [f for f in os.listdir(summaries_folder) if f.endswith(".txt") or f.endswith(".pdf")]

            summaries_info = []
            for summary in summaries:
                filepath = os.path.join(summaries_folder, summary)
                file_info = os.stat(filepath)
                size_kb = round(file_info.st_size / 1024, 2)
                last_modified = datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                summaries_info.append((summary, size_kb, last_modified))

            sort_index = {"Name": 0, "Size (KB)": 1, "Date": 2}[sort_by]
            summaries_info.sort(key=lambda x: x[sort_index], reverse=reverse)

            for summary in summaries_info:
                summaries_list.insert("", tk.END, values=summary)

        load_summaries()

        sort_order = {"Name": False, "Size (KB)": False, "Date": False}

        def on_column_click(col):
            sort_order[col] = not sort_order[col]
            load_summaries(sort_by=col, reverse=sort_order[col])

        for col in columns:
            summaries_list.heading(col, text=col, command=lambda c=col: on_column_click(c))

        # Actions
        def open_summary():
            selected = summaries_list.selection()
            if not selected:
                messagebox.showerror("Error", "No summary selected!")
                return
            filename = summaries_list.item(selected[0], "values")[0]
            filepath = os.path.join(summaries_folder, filename)

            # Open and display content
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
            elif filename.endswith(".pdf"):
                with fitz.open(filepath) as doc:
                    content = ""
                    for page in doc:
                        content += page.get_text("text")

            self.display_summary(content, "Summary")

        def delete_summary():
            selected = summaries_list.selection()
            if not selected:
                messagebox.showerror("Error", "No summary selected!")
                return
            filename = summaries_list.item(selected[0], "values")[0]
            os.remove(os.path.join(summaries_folder, filename))
            load_summaries()
            messagebox.showinfo("Delete", f"{filename} deleted successfully!")

        def rename_summary():
            selected = summaries_list.selection()
            if not selected:
                messagebox.showerror("Error", "No summary selected!")
                return
            old_filename = summaries_list.item(selected[0], "values")[0]
            rename_window = tk.Toplevel(summaries_window)
            rename_window.title("Rename Summary")

            # Ustawienie minimalnego rozmiaru okna
            rename_window.minsize(300, 150)

            ttk.Label(rename_window, text="Enter new name (without extension):").pack(pady=10)
            new_name_var = tk.StringVar(value=os.path.splitext(old_filename)[0])
            new_name_entry = ttk.Entry(rename_window, textvariable=new_name_var)
            new_name_entry.pack(pady=5)

            # Konfiguracja okna, aby pojawiało się na środku ekranu
            rename_window.update_idletasks()  # Aktualizuje informacje o geometrii okna
            window_width = rename_window.winfo_width()
            window_height = rename_window.winfo_height()

            screen_width = rename_window.winfo_screenwidth()
            screen_height = rename_window.winfo_screenheight()

            position_x = (screen_width // 2) - (window_width // 2)
            position_y = (screen_height // 2) - (window_height // 2)

            rename_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

            def apply_rename():
                new_name = new_name_var.get().strip()
                if not new_name:
                    messagebox.showerror("Error", "Name cannot be empty!")
                    return
                new_filename = f"{new_name}{os.path.splitext(old_filename)[1]}"
                os.rename(
                    os.path.join(summaries_folder, old_filename),
                    os.path.join(summaries_folder, new_filename)
                )
                load_summaries()
                rename_window.destroy()
                messagebox.showinfo("Rename", f"Renamed to {new_filename}")

            ttk.Button(rename_window, text="Rename", command=apply_rename).pack(pady=10)

        # Buttons
        button_frame = ttk.Frame(summaries_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Open", command=open_summary).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Delete", command=delete_summary).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Rename", command=rename_summary).grid(row=0, column=2, padx=10)

    def browse_recordings(self):
        recordings_window = tk.Toplevel()
        recordings_window.title("Available Recordings")
        recordings_window.geometry("700x600")

        ttk.Label(recordings_window, text="Available Recordings:", font=("Helvetica", 14)).pack(pady=10)

        # Listbox with additional information
        listbox_frame = ttk.Frame(recordings_window)
        listbox_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        columns = ("Name", "Size (MB)", "Date")
        recordings_list = ttk.Treeview(listbox_frame, columns=columns, show="headings", height=15)
        recordings_list.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            recordings_list.heading(col, text=col, anchor=tk.CENTER)

        # Adjust column widths
        recordings_list.column("Name", anchor=tk.W, width=300)
        recordings_list.column("Size (MB)", anchor=tk.E, width=100)
        recordings_list.column("Date", anchor=tk.W, width=200)

        # Load recordings into the list
        def load_recordings(sort_by="Name", reverse=False):
            for row in recordings_list.get_children():
                recordings_list.delete(row)

            recordings = [
                f for f in os.listdir(self.recordings_folder)
                if f.endswith(('.wav', '.mp3'))
            ]

            recordings_info = []
            for rec in recordings:
                filepath = os.path.join(self.recordings_folder, rec)
                file_info = os.stat(filepath)
                size_mb = round(file_info.st_size / (1024 * 1024), 2)  # Round to 2 decimal places
                last_modified = datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                recordings_info.append((rec, size_mb, last_modified))

            sort_index = {"Name": 0, "Size (MB)": 1, "Date": 2}[sort_by]
            recordings_info.sort(key=lambda x: x[sort_index], reverse=reverse)

            for rec in recordings_info:
                recordings_list.insert("", tk.END, values=rec)

        # Initial load
        load_recordings()

        # Sort on column click
        sort_order = {"Name": False, "Size (MB)": False, "Date": False}

        def on_column_click(col):
            sort_order[col] = not sort_order[col]  # Toggle sort order
            load_recordings(sort_by=col, reverse=sort_order[col])

        for col in columns:
            recordings_list.heading(col, text=col, command=lambda c=col: on_column_click(c))

        # Actions
        def play_recording():
            selected = recordings_list.selection()
            if not selected:
                messagebox.showerror("Error", "No recording selected!")
                return
            filename = recordings_list.item(selected[0], "values")[0]
            os.startfile(os.path.join(self.recordings_folder, filename))

        def delete_recording():
            selected = recordings_list.selection()
            if not selected:
                messagebox.showerror("Error", "No recording selected!")
                return
            filename = recordings_list.item(selected[0], "values")[0]
            os.remove(os.path.join(self.recordings_folder, filename))
            load_recordings()
            messagebox.showinfo("Delete", f"{filename} deleted successfully!")

        def rename_recording():
            selected = recordings_list.selection()
            if not selected:
                messagebox.showerror("Error", "No recording selected!")
                return
            old_filename = recordings_list.item(selected[0], "values")[0]
            rename_window = tk.Toplevel(recordings_window)
            rename_window.title("Rename Recording")

            # Ustawienie minimalnego rozmiaru okna
            rename_window.minsize(300, 150)

            ttk.Label(rename_window, text="Enter new name (without extension):").pack(pady=10)
            new_name_var = tk.StringVar(value=os.path.splitext(old_filename)[0])
            new_name_entry = ttk.Entry(rename_window, textvariable=new_name_var)
            new_name_entry.pack(pady=5)

            # Konfiguracja okna, aby pojawiało się na środku ekranu
            rename_window.update_idletasks()  # Aktualizuje informacje o geometrii okna
            window_width = rename_window.winfo_width()
            window_height = rename_window.winfo_height()

            screen_width = rename_window.winfo_screenwidth()
            screen_height = rename_window.winfo_screenheight()

            position_x = (screen_width // 2) - (window_width // 2)
            position_y = (screen_height // 2) - (window_height // 2)

            rename_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

            def apply_rename():
                new_name = new_name_var.get().strip()
                if not new_name:
                    messagebox.showerror("Error", "Name cannot be empty!")
                    return
                new_filename = f"{new_name}{os.path.splitext(old_filename)[1]}"
                os.rename(
                    os.path.join(self.recordings_folder, old_filename),
                    os.path.join(self.recordings_folder, new_filename)
                )
                load_recordings()
                rename_window.destroy()
                messagebox.showinfo("Rename", f"Renamed to {new_filename}")

            ttk.Button(rename_window, text="Rename", command=apply_rename).pack(pady=10)


        # Centered Buttons
        button_frame = ttk.Frame(recordings_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Play", command=play_recording).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Delete", command=delete_recording).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Rename", command=rename_recording).grid(row=0, column=2, padx=10)

    def open_settings(self):
        if self.is_recording:
            messagebox.showinfo("Settings", "Stop the recording before opening settings!")
            return

        settings_window = tk.Toplevel()
        settings_window.title("Settings")
        settings_window.geometry("400x400")  # Zwiększyłem wysokość, aby pomieścić nowe opcje

        # Wybór języka
        ttk.Label(settings_window, text="Choose Language:").pack(pady=10)

        language_var = tk.StringVar(value="Polski")

        ttk.Radiobutton(settings_window, text="Polski", variable=language_var, value="Polski").pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(settings_window, text="English", variable=language_var, value="English").pack(anchor=tk.W, padx=10)

        # Format nagrania
        ttk.Label(settings_window, text="Choose Recording Format:").pack(pady=10)

        format_var = tk.StringVar(value=self.audio_format)

        ttk.Radiobutton(settings_window, text="WAV", variable=format_var, value="wav").pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(settings_window, text="MP3", variable=format_var, value="mp3").pack(anchor=tk.W, padx=10)

        # Maksymalne miejsce
        ttk.Label(settings_window, text="Set Maximum Disk Space (MB):").pack(pady=10)

        max_space_var = tk.IntVar(value=getattr(self, "max_disk_space", 500))  # Domyślnie 500 MB
        ttk.Entry(settings_window, textvariable=max_space_var).pack(pady=5)

        # Jakość nagrania
        ttk.Label(settings_window, text="Choose Recording Quality:").pack(pady=10)

        quality_var = tk.StringVar(value=getattr(self, "recording_quality", "medium"))  # Domyślnie "medium"

        ttk.Radiobutton(settings_window, text="Low", variable=quality_var, value="low").pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(settings_window, text="Medium", variable=quality_var, value="medium").pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(settings_window, text="High", variable=quality_var, value="high").pack(anchor=tk.W, padx=10)

        # Funkcja zapisu ustawień
        def save_settings():
            self.audio_format = format_var.get()
            self.max_disk_space = max_space_var.get()
            self.recording_quality = quality_var.get()
            messagebox.showinfo("Settings", "Settings saved.")
            settings_window.destroy()

        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=20)

    def start_ui(self):
        root = tk.Tk()
        root.title("Meeting Recorder")
        root.geometry("1200x800")

        header = ttk.Label(root, text="Meeting Recorder Application", font=("Helvetica", 16, "bold"))
        header.pack(pady=20)

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Start Recording", command=self.start_audio_recording, bootstyle="success").grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Stop Recording", command=self.stop_audio_recording, bootstyle="danger").grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Save Notes", command=self.save_notes, bootstyle="warning").grid(row=0, column=2, padx=10)
        ttk.Button(button_frame, text="Summarize Notes", command=self.summarize_notes, bootstyle="warning").grid(row=0, column=3, padx=10)
        ttk.Button(button_frame, text="Browse Recordings", command=self.browse_recordings).grid(row=0, column=6, padx=10)
        ttk.Button(button_frame, text="Browse Notes", command=self.browse_notes).grid(row=0, column=4, padx=10)
        ttk.Button(button_frame, text="Browse Summaries", command=self.browse_summaries).grid(row=0, column=5, padx=10, pady=5)
        ttk.Button(button_frame, text="Settings", command=self.open_settings, bootstyle="outline-dark").grid(row=0, column=7, padx=10)

        transcription_label = ttk.Label(root, text="Transcription:", font=("Helvetica", 12))
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
