import pyaudio
import numpy as np
import threading
import time


class AudioController:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100

        self.SILENCE_THRESHOLD = 500
        self.LOUD_THRESHOLD = 2500

        # Поточний стан
        self.current_action = "IDLE"

        self.sound_start_time = 0
        self.is_sound_active = False
        self.running = True

        self.p = pyaudio.PyAudio()
        self.thread = threading.Thread(target=self._listen_mic, daemon=True)
        self.thread.start()

    def _listen_mic(self):
        try:
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
        except Exception as e:
            print(f"[ПОМИЛКА МІКРОФОНА] Не вдалося відкрити мікрофон: {e}")
            return

        while self.running:
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()

                now = time.time()

                if volume > self.SILENCE_THRESHOLD:
                    if not self.is_sound_active:
                        self.is_sound_active = True
                        self.sound_start_time = now

                    duration = now - self.sound_start_time

                    if volume >= self.LOUD_THRESHOLD:
                        if duration > 0.3:
                            self.current_action = "RUN"
                    else:
                        if duration > 0.3:
                            self.current_action = "WALK"

                else:
                    if self.is_sound_active:
                        duration = now - self.sound_start_time
                        self.is_sound_active = False

                        if duration <= 0.3:
                            self.current_action = "JUMP"
                        else:
                            self.current_action = "IDLE"
                    else:
                        if self.current_action != "JUMP":
                            self.current_action = "IDLE"

            except Exception as e:
                pass

        stream.stop_stream()
        stream.close()
        self.p.terminate()

    def get_action(self):
        action = self.current_action
        if action == "JUMP":
            self.current_action = "IDLE"
        return action

    def stop(self):
        self.running = False