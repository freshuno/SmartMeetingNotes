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

AudioSegment.converter = which("ffmpeg")


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

def summarize_with_sklearn(text, num_sentences=3):
    """
    Podsumowywanie tekstu za pomocą TF-IDF i cosine similarity (dla polskiego).
    """
    # Lematizacja tekstu
    #text = lemmatize_text(text)

    # Tokenizacja tekstu na zdania
    #sentences = nltk.sent_tokenize(text, language="polish")
    # Podziel tekst na linie (przerwy w mowie)
    sentences = text.split('\n')

    if len(sentences) <= num_sentences:
        return text

    # TF-IDF Vectorizer (z lematyzacją tylko do analizy)
    lemmatized_sentences = [lemmatize_text(sentence) for sentence in sentences]
    tfidf = TfidfVectorizer(stop_words=polish_stop_words)
    tfidf_matrix = tfidf.fit_transform(lemmatized_sentences)

    # Oblicz macierz podobieństwa kosinusowego
    sentence_scores = tfidf_matrix.sum(axis=1)

    # Posortuj zdania wg ich wyników TF-IDF
    ranked_sentences = [
        (i, sentence_scores[i, 0]) for i in range(len(sentences))
    ]
    ranked_sentences = sorted(ranked_sentences, key=lambda x: x[1], reverse=True)

    # Wybierz najlepsze zdania
    top_sentence_indices = [ranked_sentences[i][0] for i in range(num_sentences)]
    top_sentence_indices.sort()  # Sortowanie chronologiczne

    # Złóż podsumowanie
    summary = " ".join([sentences[i] for i in top_sentence_indices])

    return summary

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

        # Folder na notatki
        notes_folder = "./notes"
        if not os.path.exists(notes_folder):
            os.makedirs(notes_folder)

        # Tworzenie unikalnej nazwy pliku
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        txt_filename = os.path.join(notes_folder, f"notes_{timestamp}.txt")

        # Zapis w formacie TXT
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(self.transcription)

        messagebox.showinfo("Save Notes", f"Notes saved as:\n- {txt_filename}")

    def summarize_notes(self):
        """
        Pobiera tekst z obszaru tekstowego i generuje podsumowanie, a następnie zapisuje je do pliku.
        """
        # Pobierz tekst z notatek (obszar tekstowy)
        text = self.transcription_text.get("1.0", tk.END).strip()

        if not text:
            messagebox.showerror("Error", "Brak notatek do podsumowania!")
            return

        try:
            # Wywołanie funkcji `summarize_with_sklearn`
            summary = summarize_with_sklearn(text, num_sentences=3)

            # Wyświetl podsumowanie w polu tekstowym
            self.transcription_text.delete("1.0", tk.END)
            self.transcription_text.insert("1.0", summary)

            # Zapisz podsumowanie do pliku
            summary_folder = "./summaries"
            if not os.path.exists(summary_folder):
                os.makedirs(summary_folder)

            # Tworzenie unikalnej nazwy pliku dla podsumowania
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            summary_filename = os.path.join(summary_folder, f"summary_{timestamp}.txt")

            # Zapisz podsumowanie w formacie TXT
            with open(summary_filename, "w", encoding="utf-8") as f:
                f.write(summary)

            messagebox.showinfo("Success", f"Podsumowanie zostało wygenerowane i zapisane jako:\n- {summary_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Nie udało się stworzyć podsumowania: {e}")

    def browse_notes(self):
        notes_window = tk.Toplevel()
        notes_window.title("Available Notes")
        notes_window.geometry("700x600")

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

            notes = [f for f in os.listdir(notes_folder) if f.endswith(".txt")]

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

            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()

            # Okno z zawartością notatki
            note_window = tk.Toplevel()
            note_window.title(filename)

            # Pole wyszukiwania
            search_frame = ttk.Frame(note_window)
            search_frame.pack(padx=10, pady=5, fill="x")

            ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var)
            search_entry.pack(side="left", padx=5, fill="x", expand=True)

            text_area = ScrolledText(note_window, wrap=tk.WORD, width=80, height=20)
            text_area.pack(padx=10, pady=10, fill="both", expand=True)
            text_area.insert(tk.END, content)
            text_area.configure(state="disabled")

            # Funkcja wyszukiwania
            def search_text():
                text_area.tag_remove("highlight", "1.0", tk.END)  # Usunięcie poprzednich podświetleń
                search_term = search_var.get().strip()
                if not search_term:
                    return

                start_idx = "1.0"
                while True:
                    start_idx = text_area.search(search_term, start_idx, nocase=1, stopindex=tk.END)
                    if not start_idx:
                        break
                    end_idx = f"{start_idx}+{len(search_term)}c"
                    text_area.tag_add("highlight", start_idx, end_idx)
                    start_idx = end_idx
                text_area.tag_config("highlight", background="yellow", foreground="black")

            search_var.trace("w", lambda *args: search_text())  # Aktualizacja podświetlenia w trakcie wpisywania

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

            ttk.Label(rename_window, text="Enter new name (without extension):").pack(pady=10)
            new_name_var = tk.StringVar(value=os.path.splitext(old_filename)[0])
            new_name_entry = ttk.Entry(rename_window, textvariable=new_name_var)
            new_name_entry.pack(pady=5)

            def apply_rename():
                new_name = new_name_var.get().strip()
                if not new_name:
                    messagebox.showerror("Error", "Name cannot be empty!")
                    return
                new_filename = f"{new_name}.txt"
                os.rename(
                    os.path.join(notes_folder, old_filename),
                    os.path.join(notes_folder, new_filename)
                )
                load_notes()
                rename_window.destroy()
                messagebox.showinfo("Rename", f"Renamed to {new_filename}")

            ttk.Button(rename_window, text="Rename", command=apply_rename).pack(pady=10)

        # Przyciski akcji
        button_frame = ttk.Frame(notes_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Open", command=open_note).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Delete", command=delete_note).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Rename", command=rename_note).grid(row=0, column=2, padx=10)

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

            ttk.Label(rename_window, text="Enter new name (without extension):").pack(pady=10)
            new_name_var = tk.StringVar(value=os.path.splitext(old_filename)[0])
            new_name_entry = ttk.Entry(rename_window, textvariable=new_name_var)
            new_name_entry.pack(pady=5)

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
        root.geometry("800x600")

        header = ttk.Label(root, text="Meeting Recorder Application", font=("Helvetica", 16, "bold"))
        header.pack(pady=20)

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Start Recording", command=self.start_audio_recording).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Stop Recording", command=self.stop_audio_recording).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Save Notes", command=self.save_notes).grid(row=0, column=2, padx=10)
        ttk.Button(button_frame, text="Summarize Notes", command=self.summarize_notes).grid(row=0, column=6, padx=10)
        ttk.Button(button_frame, text="Browse Recordings", command=self.browse_recordings).grid(row=0, column=3, padx=10)
        ttk.Button(button_frame, text="Browse Notes", command=self.browse_notes).grid(row=0, column=4, padx=10)
        ttk.Button(button_frame, text="Settings", command=self.open_settings).grid(row=0, column=5, padx=10)

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
