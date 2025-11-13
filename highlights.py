import subprocess
import tempfile
import shlex
import os
from pathlib import Path
import whisper
import imageio_ffmpeg as ffmpeg

# Load Whisper model
model = whisper.load_model("base")

def video_to_audio(video_path: str) -> str:
    """
    Converts video to WAV audio for Whisper transcription using imageio-ffmpeg
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    tmp.flush()
    tmp.close()
    ffmpeg_bin = ffmpeg.get_ffmpeg_exe()
    cmd = f'{ffmpeg_bin} -y -i {shlex.quote(str(Path(video_path).resolve()))} -ar 16000 -ac 1 -vn {shlex.quote(tmp.name)}'
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("FFmpeg error:", e.stderr.decode())
        raise
    return tmp.name

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
        probe = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_format',video_path], capture_output=True)
        import json
        info = json.loads(probe.stdout)
        dur = float(info['format']['duration'])
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
