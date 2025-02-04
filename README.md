# SmartMeetingNotes

## Opis projektu
**SmartMeetingNotes** to zaawansowana aplikacja desktopowa, która umożliwia nagrywanie, transkrypcję, podsumowywanie oraz zarządzanie notatkami i materiałami ze spotkań. Dzięki rozbudowanemu interfejsowi oraz nowoczesnym algorytmom AI, aplikacja ułatwia organizację i analizę treści spotkań.

## Zestaw pytań

| Pytanie                                                                   | Odpowiedź                                                                                                     | Uwagi                                                                                                    |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Jak rozpocząć nagrywanie audio?**                               | Kliknij przycisk Start Recording.                                                                     | Nagrywanie odbywa się w formacie WAV lub MP3.                  |
| **Jak zatrzymać nagrywanie audio?**                                | Kliknij przycisk Stop Recording.                                                       | Plik dźwiękowy zostanie zapisany w folderze recordings.                   |
| **Gdzie zapisywane są nagrania?**                 | W katalogu recordings/, pliki nazwane według daty i godziny nagrania. | Można je przeglądać za pomocą funkcji browse_recordings().                                        |
| **Czy aplikacja obsługuje transkrypcję nagrań?**                   | Tak, aplikacja dokonuje transkrypcji w czasie rzeczywistym oraz po zakończeniu nagrania.                                  | Transkrypcja oparta na modelu VOSK.                                |
| **Czy aplikacja generuje podsumowania?**                | Tak, można wygenerować podsumowanie transkrypcji klikając przycisk Summarize Notes.                                      | Podsumowanie tworzone jest z pomocą Cohere AI.                                 |
| **Czy aplikacja obsługuje pliki PDF?**                     | Tak, można zapisywać notatki jako PDF oraz przeglądać zapisane dokumenty.                                                   | Używana biblioteka ReportLab.                                    |
| **Jak działa opcja przeglądania zapisanych notatek?**    | Użyj przycisku Browse Notes, aby zobaczyć listę dostępnych notatek.         | Notatki można edytować, usuwać i zmieniać ich nazwy.                                                |
| **Czy aplikacja obsługuje zrzuty ekranu?**                               | Tak, podczas nagrywania są wykonywane automatyczne zrzuty ekranu w ustalonych odstępach czasu.    | Zrzuty ekranu są zapisywane w folderze screenshots.              |

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


## Interfejs
![image](https://github.com/user-attachments/assets/5d8ead95-ddc0-48d7-9be4-efe559d1ea01)

![image](https://github.com/user-attachments/assets/fcc522fc-86f2-47b4-9039-66bd4cf084bb)



## Instrukcja uruchomienia

Pełna instrukcja uruchomienia projektu znajduje się w pliku [setup.md](https://github.com/freshuno/SmartMeetingNotes/blob/main/docs/setup.md) w folderze `docs` i opisuje:
   - instalację środowiska Python
   - instalację zależności
   - konfigurację zmiennych środowiskowych

