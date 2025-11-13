import subprocess, sys
from pathlib import Path
import tempfile

# Ensure Whisper is installed
try:
    import whisper
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "openai-whisper"])
    import whisper

# Load Whisper model ('base' recommended for Streamlit Cloud)
model = whisper.load_model("base")

ASS_TEMPLATE = """
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTok,Impact,72,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,8,10,10,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def generate_ass_captions(video_path: str, style: str = 'TikTok'):
    result = model.transcribe(video_path, word_timestamps=True)
    segments = result.get('segments', [])

    ass_path = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".ass").name)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_TEMPLATE)
        for seg in segments:
            def fmt(t):
                h = int(t//3600)
                m = int((t%3600)//60)
                s = int(t%60)
                cs = int((t - int(t)) * 100)
                return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"
            f.write(f"Dialogue: 0,{fmt(seg['start'])},{fmt(seg['end'])},TikTok,,0,0,0,,{seg['text']}\n")
    return str(ass_path)

def burn_ass_subtitles(video_path: str, ass_path: str, output_dir: Path):
    outp = output_dir / (Path(video_path).stem + "_final.mp4")
    cmd = f"ffmpeg -y -i {subprocess.list2cmdline([video_path])} -vf ass={subprocess.list2cmdline([ass_path])} -c:v libx264 -c:a aac -movflags +faststart {subprocess.list2cmdline([str(outp)])}"
    subprocess.run(cmd, shell=True, check=True)
    return str(outp)
