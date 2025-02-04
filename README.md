# SmartMeetingNotes

## Opis projektu
**SmartMeetingNotes** to zaawansowana aplikacja desktopowa, która umożliwia nagrywanie, transkrypcję, podsumowywanie oraz zarządzanie notatkami i materiałami ze spotkań. Dzięki rozbudowanemu interfejsowi oraz nowoczesnym algorytmom AI, aplikacja ułatwia organizację i analizę treści spotkań.

## Funkcjonalności
1. **Interfejs użytkownika (GUI)**:
   - Zbudowany przy użyciu **Tkinter** i **ttkbootstrap**.
   - Intuicyjne okno z przyciskami umożliwia:
     - Rozpoczęcie i zakończenie nagrywania.
     - Wyświetlenie transkrypcji w czasie rzeczywistym.
     - Przeglądanie, podsumowywanie i zarządzanie nagraniami oraz notatkami.

2. **Nagrywanie i przetwarzanie dźwięku**:
   - Nagrania są realizowane przy pomocy **Soundcard**.
   - Obsługiwane formaty: WAV i MP3.
   - Transkrypcje generowane dzięki silnikowi **Vosk** (model języka polskiego).

3. **Podsumowanie notatek**:
   - Tworzenie podsumowań tekstowych za pomocą **Cohere AI**.
     
4. **Zapisywanie i zarządzanie plikami**:
   - Notatki i podsumowania można zapisać w formatach:
     - **TXT**
     - **PDF** (generowany za pomocą **ReportLab**).
   - Wbudowane narzędzia do przeglądania, usuwania, zmiany nazw oraz sortowania plików.

5. **Analiza zdjęć OCR**:
   - Przetwarzanie tekstu z obrazów i zrzutów ekranu.
   - Wykorzystanie pytesseract do rozpoznawania tekstu na obrazach.


## Struktura projektu
- **Meeting Recorder Application**
  - `recordings/` – Folder na pliki audio.
  - `notes/` – Folder na zapisane notatki.
  - `summaries/` – Folder na podsumowania.
  - `screenshots/` – Folder na zrzuty ekranu.
  - `vosk-model/` – Model językowy Vosk.
  - `main.py` – Główny plik aplikacji.
  - `requirements.txt` – Lista zależności wymaganych do uruchomienia projektu.
  - `DejaVuSans.ttf` – Czcionka.
  - `docs/`
  - `└── setup.md` - Instrukcja instalacji i uruchomienia.

## Technologie użyte w projekcie

- **Nagrywanie i transkrypcja audio**:
  - [Vosk](https://alphacephei.com/vosk), [Soundcard](https://pypi.org/project/soundcard/)
- **Generowanie podsumowań**:
  - [Cohere API](https://cohere.com/)
- **Generowanie plików PDF**:
  - [ReportLab](https://www.reportlab.com/)
- **Interfejs graficzny**:
  - [Tkinter](https://docs.python.org/3/library/tkinter.html), [ttkbootstrap](https://ttkbootstrap.readthedocs.io/)
- **Analiza obrazów**:
  - [pytesseract](https://pypi.org/project/pytesseract/), [PIL](https://pypi.org/project/pillow/)



## Instrukcja uruchomienia

Pełna instrukcja uruchomienia projektu znajduje się w pliku [setup.md](https://github.com/freshuno/SmartMeetingNotes/blob/main/docs/setup.md) w folderze `docs` i opisuje:
   - instalację środowiska Python
   - instalację zależności
   - konfigurację zmiennych środowiskowych

