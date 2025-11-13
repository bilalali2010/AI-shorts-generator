import tempfile
import os
from pathlib import Path
import whisper
import ffmpeg  # Python wrapper
import json

# Load Whisper model
model = whisper.load_model("base")

def video_to_audio(video_path: str) -> str:
    """
    Converts video to WAV audio for Whisper using ffmpeg-python
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    tmp.close()
    out_path = tmp.name
    try:
        (
            ffmpeg
            .input(str(Path(video_path).resolve()))
            .output(out_path, ar=16000, ac=1, vn=None)
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())
        raise
    return out_path

def find_best_highlight(video_path: str, target_seconds: int = 45):
    audio_path = video_to_audio(video_path)
    try:
        result = model.transcribe(audio_path, word_timestamps=True)
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

    segments = result.get('segments', [])
    if not segments:
        # fallback: center clip
        probe = ffmpeg.probe(str(video_path))
        dur = float(probe['format']['duration'])
        start = max(0, dur/2 - target_seconds/2)
        return float(start), float(start + target_seconds)

    # Sliding window to find highlight
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
