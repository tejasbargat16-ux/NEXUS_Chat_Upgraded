"""
Push-to-talk voice subsystem for NEXUS v2 desktop.
Provides push-to-talk recording, speech recognition (Groq Whisper / SpeechRecognition),
offline text-to-speech (pyttsx3), and hotkey management.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable

logger = logging.getLogger("nexus.desktop.voice")


def speak(text: str) -> bool:
    """Speak text aloud using the configured TTS engine."""
    clean_text = text.strip()
    if not clean_text:
        return False

    try:
        from core.voice import speak as core_speak
        core_speak(clean_text)
        return True
    except Exception as exc:
        logger.warning("TTS speech failed: %s", exc)
        return False


def record_and_transcribe(duration: float = 5.0) -> str:
    """Record audio from microphone for specified duration and transcribe to text."""
    try:
        from core.voice import record_mic_desktop, transcribe_groq
        from core.llm import load_key

        rec_dir = os.path.expanduser("~/.nexuschat")
        os.makedirs(rec_dir, exist_ok=True)
        rec_path = os.path.join(rec_dir, "voice_input.wav")

        record_mic_desktop(duration, rec_path)
        if not os.path.exists(rec_path):
            return ""

        groq_key = load_key("groq")
        if groq_key:
            try:
                return transcribe_groq(rec_path, groq_key)
            except Exception as e:
                logger.debug("Groq transcribe failed, falling back: %s", e)

        # Fallback to SpeechRecognition offline/Google free tier
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(rec_path) as source:
            audio = r.record(source)
            return r.recognize_google(audio)
    except Exception as exc:
        logger.warning("Voice transcription failed: %s", exc)
        return ""


class PushToTalkManager:
    """Manages push-to-talk hotkey triggers using pynput."""

    def __init__(self, callback: Callable[[str], None] | None = None):
        self.callback = callback
        self._listener = None
        self._is_recording = False

    def start(self) -> bool:
        """Start global hotkey listener for push-to-talk."""
        try:
            from pynput import keyboard

            # Trigger on Ctrl+Space
            current_keys = set()

            def on_press(key):
                current_keys.add(key)
                if (
                    keyboard.Key.ctrl in current_keys or keyboard.Key.ctrl_l in current_keys or keyboard.Key.ctrl_r in current_keys
                ) and keyboard.Key.space in current_keys:
                    if not self._is_recording:
                        self._is_recording = True
                        threading.Thread(target=self._handle_voice_turn, daemon=True).start()

            def on_release(key):
                current_keys.discard(key)

            self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception as exc:
            logger.warning("Failed to initialize pynput hotkey listener: %s", exc)
            return False

    def stop(self) -> None:
        """Stop hotkey listener."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _handle_voice_turn(self) -> None:
        try:
            logger.info("Push-to-talk triggered. Recording...")
            text = record_and_transcribe(duration=4.0)
            if text and self.callback:
                self.callback(text)
        finally:
            self._is_recording = False
