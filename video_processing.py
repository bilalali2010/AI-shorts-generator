import subprocess
from pathlib import Path
import tempfile
import shlex
import imageio_ffmpeg as ffmpeg

# Get ffmpeg binary path
FFMPEG_BIN = ffmpeg.get_ffmpeg_exe()

def run(cmd):
    print('RUN:', cmd)
    completed = subprocess.run(shlex.split(cmd), capture_output=True)
    if completed.returncode != 0:
        print('ERR', completed.stderr.decode())
        raise RuntimeError('Command failed')
    return completed.stdout

def download_youtube(url: str) -> str:
    """
    Download YouTube video using yt-dlp
    """
    out = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    out.close()
    cmd = f"yt-dlp -f 'bv+ba/best' -o {out.name} {shlex.quote(url)}"
    run(cmd)
    return out.name

def extract_clip(video_path: str, start: float, end: float, output_dir: Path) -> str:
    """
    Extract a clip from the video
    """
    outp = output_dir / f"clip_{int(start)}_{int(end)}.mp4"
    duration = end - start
    cmd = f"{FFMPEG_BIN} -y -ss {start} -i {shlex.quote(str(video_path))} -t {duration} -c:v libx264 -c:a aac -movflags +faststart {shlex.quote(str(outp))}"
    run(cmd)
    return str(outp)

def reframe_vertical(clip_path: str, output_dir: Path) -> str:
    """
    Crop and scale video to vertical (1080x1920)
    """
    outp = output_dir / (Path(clip_path).stem + '_v.mp4')
    cmd = (
        f"{FFMPEG_BIN} -y -i {shlex.quote(clip_path)} "
        f"-vf \"scale='if(gt(a,1080/1920),-2,1080)':'if(gt(a,1080/1920),1920,-2)',crop=1080:1920\" "
        f"-c:v libx264 -c:a aac {shlex.quote(str(outp))}"
    )
    run(cmd)
    return str(outp)
