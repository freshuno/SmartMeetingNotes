# SmartMeetingNotes

## Instalacja aplikacji

1.  **Klonowanie repozytorium:**
    ```bash
    git clone https://github.com/freshuno/SmartMeetingNotes.git
    ```

2.  **Stworzenie i aktywacja środowiska wirtualnego:**
    ```bash
    cd SmartMeetingNotes/
    python -m venv venv
    source venv/bin/activate # Linux/macOS
    venv\Scripts\activate # Windows
    ```
    
3.  **Instalacja zależności:**
    ```bash
    pip install -r requirements.txt
    pip install numpy
    pip install soundcard
    pip install soundfile
    pip install vosk
    pip install fpdf
    pip install pydub
    pip install openai
    pip install nltk
    pip install scikit-learn
    pip install spacy
    pip install ttkbootstrap
    pip install reportlab
    pip install fitz
    pip install frontend
    pip install tools
    pip install pyautogui
    pip install pytesseract
    ```

4. **Instalacja Tesseract:**
   - wejdź w link https://github.com/UB-Mannheim/tesseract/wiki
   - pobierz i zainstaluj Tesseract
   - wykonaj następujące kroki:
     
   ![image](https://github.com/user-attachments/assets/785061a1-794a-4d36-a9c2-4809ec6749cc)

   - w pliku main.py zaaktualizuj linijkę:

     ```bash
     pytesseract.pytesseract.tesseract_cmd = r'E:\Tesseract\tesseract.exe'
     ```
     tak żeby odpowiadała lokalizacji na Twoim komputerze
     
5. **Uruchamianie aplikacji:**
   ```bash
    python main.py
    ```
