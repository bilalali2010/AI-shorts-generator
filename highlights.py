import subprocess, sys
import tempfile
import json

# Ensure Whisper is installed (works on Streamlit Cloud)
try:
    import whisper
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "openai-whisper"])
    import whisper

# Load Whisper model ('base' is smaller and faster for Streamlit Cloud)
model = whisper.load_model("base")

def find_best_highlight(video_path: str, target_seconds: int = 45):
    # Transcribe video with Whisper (timestamps enabled)
    result = model.transcribe(video_path, word_timestamps=True)
    segments = result.get('segments', [])

    if not segments:
        # fallback: center clip
        probe = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_format',video_path], capture_output=True)
        info = json.loads(probe.stdout)
        dur = float(info['format']['duration'])
        start = max(0, dur/2 - target_seconds/2)
        return float(start), float(start + target_seconds)

    # Sliding window heuristic to find highest word density
    best_score = -1
    best_start = 0
    total_duration = segments[-1]['end']
    step = 5
    for s in range(0, int(total_duration)-target_seconds, step):
        e = s + target_seconds
        text = " ".join([seg['text'] for seg in segments if not (seg['end'] < s or seg['start'] > e)])
        words = len(text.split())
        if words > best_score:
            best_score = words
            best_start = s
    return float(best_start), float(best_start + target_seconds)
