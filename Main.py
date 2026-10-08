import asyncio
import threading
import time
import os

# Conditional imports to prevent crash on import
try:
    from Frontend.GUI import JarvisHUD as JarvisUI
except ImportError:
    JarvisUI = None

try:
    from Backend.SpeechToText import Listen, get_mic_level, start_mic_monitoring
except ImportError:
    Listen, get_mic_level, start_mic_monitoring = None, None, None

try:
    from Backend.TextToSpeech import Speak, NeuralSpeak, set_speech_callback
except ImportError:
    Speak, NeuralSpeak, set_speech_callback = None, None, None

from PyQt5.QtCore import qInstallMessageHandler

def qt_message_handler(mode, context, message):
    pass

qInstallMessageHandler(qt_message_handler)

try:
    from Backend.Model import Router
except ImportError:
    Router = None

def mic_monitor(ui):
    """Continuously poll mic level from the running monitor."""
    if not get_mic_level: return
    while True:
        try:
            level = get_mic_level()
            ui.set_audio_level(level, source="mic")
        except Exception:
            pass
        time.sleep(0.05)

def log_crash(error):
    with open("crash_log.txt", "a") as f:
        f.write(f"[{time.ctime()}] {error}\n")

def jarvis_main_loop(ui):
    """Wait for voice command and process it."""
    if not Listen: return
    while True:
        try:
            # Mic OFF → stay IDLE, poll until user turns mic back on
            if not ui.get_mic_active():
                ui.update_status("IDLE")
                time.sleep(0.3)
                continue

            # Mic ON → stay LISTENING the entire time
            ui.update_status("LISTENING")
            query = Listen()

            # If mic was turned off during the listen call, honour that
            if not ui.get_mic_active():
                ui.update_status("IDLE")
                continue

            if query:
                ui.set_transcription(query)
                ui.update_status("PROCESSING")
                if Router:
                    response = Router(query)
                    ui.set_response(response)
                    ui.update_status("SPEAKING")
                    if NeuralSpeak:
                        asyncio.run(NeuralSpeak(response))
                # Go straight back to LISTENING (no IDLE dip) if mic still on
                # (next iteration handles the state update)
            # No sleep here — loop immediately back to LISTENING
        except RuntimeError:
            # UI closed / C++ object deleted
            break
        except Exception as e:
            log_crash(f"Loop Error: {e}")
            try:
                ui.update_status("ERROR")
            except RuntimeError:
                break
            time.sleep(3)

def start_system():
    # Clear logs
    if os.path.exists("crash_log.txt"):
        try:
            os.remove("crash_log.txt")
        except: pass
            
    print("Initializing JARVIS Holographic Systems...")
    try:
        if not JarvisUI:
            print("FATAL: JarvisUI not found")
            return

        from PyQt5.QtWidgets import QApplication
        import sys
        
        qt_app = QApplication(sys.argv)
        ui = JarvisUI()

        # Wire edge-tts callback → FFT visualizer (redundant safety, GUI also wires it)
        if set_speech_callback:
            try:
                set_speech_callback(ui.core_hud.notify_speech_start)
            except Exception as e:
                log_crash(f"Callback Wire Error: {e}")
        
        if start_mic_monitoring:
            try:
                start_mic_monitoring()
            except Exception as e:
                log_crash(f"Mic Setup Error: {e}")
        
        # Start logical threads
        logic_thread = threading.Thread(target=lambda: jarvis_main_loop(ui), daemon=True)
        mic_thread = threading.Thread(target=lambda: mic_monitor(ui), daemon=True)
        
        logic_thread.start()
        mic_thread.start()
        
        # Startup Voice
        def delayed_voice():
            time.sleep(3)
            if Speak:
                try:
                    ui.update_status("SPEAKING")
                    Speak("Systems online. Holographic core engaged.")
                    ui.update_status("LISTENING" if ui.get_mic_active() else "IDLE")
                except Exception as e:
                    log_crash(f"Startup Voice Error: {e}")
                
        threading.Thread(target=delayed_voice, daemon=True).start()

        print("Main: Launching HUB Interface...")
        ui.show()
        sys.exit(qt_app.exec_())
        
    except Exception as e:
        log_crash(f"FATAL ERROR: {e}")
        print(f"FATAL ERROR: {e}")
        time.sleep(5)

if __name__ == "__main__":
    start_system()
