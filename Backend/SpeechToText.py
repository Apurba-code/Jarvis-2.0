import speech_recognition as sr
import pyaudio
import audioop
import threading
import time

class MicLevelMonitor:
    def __init__(self):
        self.level = 0.0
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _monitor(self):
        CHUNK = 1024
        p = None
        stream = None
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=CHUNK)
            while self.running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    rms = audioop.rms(data, 2)
                    self.level = min(rms / 1500.0, 1.0)
                except Exception:
                    break
                time.sleep(0.01)
        except Exception:
            pass
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception: pass
            if p:
                try:
                    p.terminate()
                except Exception: pass

_monitor_instance = MicLevelMonitor()

def start_mic_monitoring():
    _monitor_instance.start()

def get_mic_level():
    return _monitor_instance.level

def Listen():
    _monitor_instance.stop() # Ensure mic is free
    
    r = sr.Recognizer()
    query = ""
    try:
        with sr.Microphone() as source:
            r.pause_threshold = 0.8
            r.adjust_for_ambient_noise(source, duration=0.3)
            audio = r.listen(source, timeout=8, phrase_time_limit=10)
        
        query = r.recognize_google(audio, language="en-in")
        query = query.lower()
    except Exception:
        pass
    finally:
        _monitor_instance.start() # Resume monitoring
        
    return query

if __name__ == "__main__":
    while True:
        Listen()
