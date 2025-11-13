import subprocess, shlex
from pathlib import Path
import tempfile

def run(cmd):
    print('RUN:', cmd)
    completed = subprocess.run(shlex.split(cmd), capture_output=True)
    if completed.returncode != 0:
        print('ERR', completed.stderr.decode())
        raise RuntimeError('Command failed')
    return completed.stdout

def ensure_ffmpeg():
    try:
        subprocess.run(['ffmpeg','-version'], check=True, capture_output=True)
    except Exception:
        raise RuntimeError('ffmpeg not found in environment')

def download_youtube(url: str) -> str:
    out = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    out.close()
    cmd = f"yt-dlp -f 'bv+ba/best' -o {out.name} {shlex.quote(url)}"
    run(cmd)
    return out.name

def extract_clip(video_path: str, start: float, end: float, output_dir: Path) -> str:
    outp = output_dir / f"clip_{int(start)}_{int(end)}.mp4"
    duration = end - start
    cmd = f"ffmpeg -y -ss {start} -i {shlex.quote(str(video_path))} -t {duration} -c:v libx264 -c:a aac -movflags +faststart {shlex.quote(str(outp))}"
    run(cmd)
    return str(outp)

def reframe_vertical(clip_path: str, output_dir: Path) -> str:
    outp = output_dir / (Path(clip_path).stem + '_v.mp4')
    cmd = (
        f"ffmpeg -y -i {shlex.quote(clip_path)} -vf \"scale='if(gt(a,1080/1920),-2,1080)':'if(gt(a,1080/1920),1920,-2)',crop=1080:1920\" -c:v libx264 -c:a aac {shlex.quote(str(outp))}"
    )
    run(cmd)
    return str(outp)
