# JARVIS Advanced AI Assistant v2.0

A high-intelligence, modular AI voice assistant with a futuristic sci-fi GUI.

## 🌟 Features
- **Modular Architecture**: Backend, Frontend, and Data layers are completely separated.
- **Futuristic UI**: Dark-themed HUD using `CustomTkinter`.
- **Natural Speech**: Neural voices via `edge-tts`.
- **System Automation**: Control apps, browser, and OS settings.
- **Persistent Memory**: Saves conversation history to `Data/ChatLog.json`.
- **Knowledge Core**: Wikipedia and real-time Google search integration.
- **Intent Routing**: Smart routing of commands (Open, Search, Chat, System).

## 📂 Project Structure
- `Main.py`: The central orchestrator.
- `Backend/`:
  - `SpeechToText.py`: Microphone processing & wake word.
  - `TextToSpeech.py`: Standard and Neural voice engines.
  - `Model.py`: Command routing logic.
  - `Chatbot.py`: Context-aware conversational AI.
  - `Automation.py`: OS & Browser task execution.
  - `RealtimeSearchEngine.py`: Web & Wiki information retrieval.
  - `ImageGeneration.py`: AI Image generation placeholder.
- `Frontend/`:
  - `GUI.py`: CustomTkinter interface.
- `Data/`:
  - `ChatLog.json`: Memory storage.

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install customtkinter edge-tts SpeechRecognition requests psutil wikipedia openai-whisper pyaudio
   ```

2. **Run JARVIS**:
   ```bash
   python Main.py
   ```

3. **Interaction**:
   - Click "ACTIVATE JARVIS".
   - Say "Jarvis" followed by your command (e.g., "Jarvis, open Chrome and search for space news").

## 🛠 Advanced Configuration
- **Voice**: Change the voice ID or neural voice in `Backend/TextToSpeech.py`.
- **Search**: Extend `Automation.py` for more complex system tasks.
