import streamlit as st
from pathlib import Path
from video_processing import download_youtube, extract_clip, reframe_vertical, ensure_ffmpeg
from highlights import find_best_highlight
from captions import generate_ass_captions, burn_ass_subtitles
import tempfile

st.set_page_config(page_title="AI Shorts Generator — Free", layout='wide')
st.title('AI Shorts Generator — Free')

st.markdown('Paste a YouTube URL or upload a video. The app will transcribe locally via Whisper, pick a highlight, crop to vertical, add styled captions, and return a downloadable Short.')

col1, col2 = st.columns([3,1])
with col1:
    url = st.text_input('YouTube URL (leave empty to upload)')
    uploaded = st.file_uploader('Or upload a video file', type=['mp4','mov','mkv','webm'])

with col2:
    duration = st.selectbox('Short length (sec)', [30,45,60], index=2)
    style = st.selectbox('Caption style', ['TikTok (default)','MrBeast','Lower-third'], index=0)
    generate_btn = st.button('Generate Short')

output_dir = Path('outputs')
output_dir.mkdir(exist_ok=True)
if generate_btn:
    with st.spinner('Processing — this can take a few minutes'):
        if url:
            video_path = download_youtube(url)
        elif uploaded is not None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded.name.split('.')[-1])
            tmp.write(uploaded.read())
            tmp.close()
            video_path = tmp.name
        else:
            st.warning('Provide a YouTube URL or upload a file')
            st.stop()

        start, end = find_best_highlight(video_path, target_seconds=duration)
        clip_path = extract_clip(video_path, start, end, output_dir)
        vclip_path = reframe_vertical(clip_path, output_dir)

        ass_path = generate_ass_captions(vclip_path, style=style)
        final_path = burn_ass_subtitles(vclip_path, ass_path, output_dir)

    st.success('Done!')
    st.video(final_path)
    with open(final_path,'rb') as f:
        st.download_button('Download Short', data=f.read(), file_name=Path(final_path).name)
