import sys
import os
import time
import traceback

print("LAUNCHER: Starting JARVIS...")

try:
    print("LAUNCHER: Importing Frontend...")
    try:
        from Frontend.GUI import JarvisUI
    except ImportError:
        from Frontend.GUI import JarvisHUD as JarvisUI
    print("LAUNCHER: Frontend Imported.")
    
    print("LAUNCHER: Importing Backend...")
    # Conditionally import backend to allow GUI-only test
    try:
        from Backend.SpeechToText import start_mic_monitoring
        from Backend.TextToSpeech import Speak
        from Backend.Model import Router
        from Main import jarvis_main_loop, mic_monitor
        FULL_MODE = True
        print("LAUNCHER: Backend Imported. Full Mode ENABLED.")
    except Exception as e:
        print(f"LAUNCHER: Backend Import Failed: {e}")
        print("LAUNCHER: Running in GUI-ONLY Mode.")
        FULL_MODE = False

    from PyQt5.QtWidgets import QApplication
    import threading

    def start():
        app = QApplication(sys.argv)
        ui = JarvisUI()
        
        if FULL_MODE:
            print("LAUNCHER: Starting Background Threads...")
            try:
                start_mic_monitoring()
                
                logic_thread = threading.Thread(target=lambda: jarvis_main_loop(ui), daemon=True)
                mic_thread = threading.Thread(target=lambda: mic_monitor(ui), daemon=True)
                
                logic_thread.start()
                mic_thread.start()
                
                # Startup voice
                threading.Thread(target=lambda: (time.sleep(2), Speak("Online")), daemon=True).start()
                
            except Exception as e:
                print(f"LAUNCHER: Thread Error: {e}")
        
        print("LAUNCHER: Showing UI...")
        ui.show()
        sys.exit(app.exec_())

    if __name__ == "__main__":
        start()

except Exception as e:
    print(f"LAUNCHER: FATAL ERROR: {e}")
    traceback.print_exc()
    input("Press Enter to Exit...")
