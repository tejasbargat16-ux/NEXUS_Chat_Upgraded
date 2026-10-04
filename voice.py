"""
Voice input/output for NEXUS Chat.

On Windows/Mac/Linux: uses pyttsx3 (offline TTS) + SpeechRecognition (mic).
On Android/Termux:    uses termux-tts-speak + Groq Whisper (original behaviour).

No extra installs needed on Windows — pyttsx3 and SpeechRecognition are
already in the standard requirements.
"""

import os
import platform
import shutil
import subprocess
import threading
import time

import requests

VOICE_DIR = os.path.expanduser("~/.nexuschat")
RECORDING_PATH = os.path.join(VOICE_DIR, "voice_input.wav")
GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"

_IS_TERMUX = shutil.which("termux-tts-speak") is not None


# ------------------------------------------------------------------ detection

def termux_api_available():
    """Return True if running on Termux with both TTS and mic tools present."""
    return (
        shutil.which("termux-tts-speak") is not None
        and shutil.which("termux-microphone-record") is not None
    )


def voice_available():
    """Return True if any speech output/TTS backend is available (Termux OR pyttsx3)."""
    if shutil.which("termux-tts-speak") is not None:
        return True
    try:
        import pyttsx3  # noqa: F401
        return True
    except ImportError:
        return False


def mic_available():
    """Return True if microphone audio recording backend is available."""
    if shutil.which("termux-microphone-record") is not None:
        return True
    try:
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


# ------------------------------------------------------------------ TTS output

def _speak_pyttsx3(text, console):
    """Speak using pyttsx3 (Windows/Mac/Linux). Runs in a thread so the main
    thread can watch for an Enter keypress to interrupt it."""
    import pyttsx3

    stop_event = threading.Event()

    def _run():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)   # words per minute
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass
        finally:
            stop_event.set()

    tts_thread = threading.Thread(target=_run, daemon=True)
    tts_thread.start()

    console.print("[dim](speaking... press Enter to interrupt)[/]")

    interrupted = threading.Event()

    def _wait_enter():
        try:
            input()
        except EOFError:
            pass
        interrupted.set()

    listener = threading.Thread(target=_wait_enter, daemon=True)
    listener.start()

    while not stop_event.is_set():
        if interrupted.is_set():
            # pyttsx3 has no cross-platform hard-stop; we signal the engine
            # to stop after the current utterance by calling stop() from
            # another thread.  It's imperfect but the best we can do without
            # blocking the main thread.
            try:
                import pyttsx3 as _p
                _engine = _p.init()
                _engine.stop()
            except Exception:
                pass
            console.print("[yellow]Interrupted.[/]")
            return
        time.sleep(0.05)


def _speak_termux(text, console):
    """Original Termux TTS with Enter-to-interrupt support."""
    proc = subprocess.Popen(
        ["termux-tts-speak", text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    console.print("[dim](speaking... press Enter to interrupt)[/]")

    stop_event = threading.Event()

    def wait_for_enter():
        try:
            input()
        except EOFError:
            pass
        stop_event.set()

    listener = threading.Thread(target=wait_for_enter, daemon=True)
    listener.start()

    while proc.poll() is None:
        if stop_event.is_set():
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            console.print("[yellow]Interrupted.[/]")
            return
        time.sleep(0.1)


def speak_with_interrupt(text, console, poll_interval=0.1):
    """
    Speak *text* aloud. Chooses Termux TTS on Android, pyttsx3 on desktop.
    While speaking, pressing Enter interrupts playback immediately.
    Silently does nothing if no voice backend is available.
    """
    if _IS_TERMUX:
        _speak_termux(text, console)
    else:
        try:
            _speak_pyttsx3(text, console)
        except Exception as e:
            console.print(f"[dim yellow]TTS unavailable: {e}[/]")


# ------------------------------------------------------------------ mic input

def record_voice_input(seconds=6):
    """
    Record audio from the microphone and return the path to a WAV file.

    On Termux:  uses termux-microphone-record.
    On Windows: uses SpeechRecognition + sounddevice (listens until silence
                or `seconds` have elapsed).
    Raises RuntimeError if no mic backend is available.
    """
    if _IS_TERMUX:
        return _record_termux(seconds)
    return _record_desktop(seconds)


def _record_termux(seconds):
    if not shutil.which("termux-microphone-record"):
        raise RuntimeError(
            "termux-microphone-record not found. Install with: pkg install termux-api "
            "(and install the Termux:API app from F-Droid/Play Store)."
        )
    os.makedirs(VOICE_DIR, exist_ok=True)
    if os.path.exists(RECORDING_PATH):
        os.remove(RECORDING_PATH)

    subprocess.run(
        ["termux-microphone-record", "-f", RECORDING_PATH, "-l", str(seconds)],
        check=True,
    )
    time.sleep(seconds + 1)
    subprocess.run(
        ["termux-microphone-record", "-q"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not os.path.exists(RECORDING_PATH):
        raise RuntimeError("Recording failed — no audio file was produced.")
    return RECORDING_PATH


def _record_desktop(seconds):
    """Record from the default microphone using sounddevice + wave."""
    try:
        import sounddevice as sd
        import wave
        import numpy as np
    except ImportError:
        raise RuntimeError(
            "sounddevice and numpy are required for mic recording on Windows/Linux/Mac.\n"
            "Install them with:  pip install -r requirements.txt"
        )

    os.makedirs(VOICE_DIR, exist_ok=True)

    sample_rate = 16000
    channels = 1
    recording = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
    )
    sd.wait()  # block until done

    with wave.open(RECORDING_PATH, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())

    return RECORDING_PATH


# ---------------------------------------------------------------- transcription

def transcribe_with_groq(api_key, audio_path):
    """Send the recorded audio to Groq's Whisper endpoint and return the text."""
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {"model": WHISPER_MODEL}
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.post(
            GROQ_TRANSCRIBE_URL, headers=headers, files=files, data=data, timeout=60
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Groq Whisper error {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("text", "").strip()


def transcribe_with_speech_recognition(audio_path, language="en-US"):
    """
    Transcribe audio using SpeechRecognition (Google Web Speech API).
    Free, zero API key required fallback for speech-to-text.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        raise RuntimeError(
            "speechrecognition is required for local/free fallback transcription.\n"
            "Install it with:  pip install -r requirements.txt"
        )

    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = r.record(source)

    try:
        return r.recognize_google(audio_data, language=language).strip()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"SpeechRecognition service error: {e}")


def transcribe_audio(audio_path, groq_key=None):
    """
    Transcribe recorded audio file.
    Prefers Groq Whisper if GROQ_API_KEY is configured.
    Seamlessly falls back to SpeechRecognition (keyless) if Groq key is absent or request fails.
    """
    if groq_key:
        try:
            return transcribe_with_groq(groq_key, audio_path)
        except Exception:
            # Fall back to speech_recognition if Groq fails
            pass

    return transcribe_with_speech_recognition(audio_path)
