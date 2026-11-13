"""Caption Studio Web -- local-first video caption editor."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
WORK = Path(tempfile.gettempdir()) / 'caption-studio-web-jobs'
WORK.mkdir(exist_ok=True)
MAX_BYTES = int(os.getenv('MAX_UPLOAD_MB', '200')) * 1024 * 1024
TTL_SECONDS = 2 * 3600
JOBS = {}
LOCK = threading.Lock()
PROCESS_LOCK = threading.Lock()
app = FastAPI(title='Caption Studio Web', version='2.0.0', docs_url=None, redoc_url=None)


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return 'ffmpeg'


def clean_old():
    now = time.time()
    with LOCK:
        old = [k for k, v in JOBS.items() if now-v['created'] > TTL_SECONDS and v['state'] not in ('processing','exporting')]
        for k in old:
            shutil.rmtree(WORK / k, ignore_errors=True)
            del JOBS[k]


def get_job(jobid):
    with LOCK:
        job = JOBS.get(jobid)
    if not job:
        raise HTTPException(404, 'Job unavailable or expired')
    return job


def report(jobid, **kwargs):
    with LOCK:
        if jobid in JOBS:
            JOBS[jobid].update(kwargs)


def run_ffmpeg(args, cwd=None):
    cmd = [ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-y', *args]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1200)
    if p.returncode:
        raise RuntimeError((p.stderr or 'FFmpeg failed')[-1400:])


@app.get('/api/health')
def health():
    return {'ok': True, 'version': '2.0.0'}


@app.post('/api/jobs')
async def upload(file: UploadFile = File(...)):
    clean_old()
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in {'.mp4', '.mov', '.mkv', '.webm', '.m4v'}:
        raise HTTPException(400, 'Supported videos: MP4, MOV, MKV, WEBM, M4V')
    with LOCK:
        if len(JOBS) >= 20:
            raise HTTPException(429, 'Server is busy; try again later')
    jobid = uuid4().hex
    folder = WORK / jobid
    folder.mkdir(mode=0o700)
    dest = folder / ('source' + suffix)
    written = 0
    try:
        with dest.open('wb') as out:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_BYTES:
                    raise HTTPException(413, 'File too large for this free server')
                out.write(chunk)
        if not written:
            raise HTTPException(400, 'Empty video file')
        job = {'created': time.time(), 'state': 'ready', 'message': 'Video ready', 'source': str(dest), 'captions': [], 'output': None}
        with LOCK:
            JOBS[jobid] = job
        return {'id': jobid, 'video_url': f'/api/jobs/{jobid}/video'}
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    finally:
        await file.close()


@app.get('/api/jobs/{jobid}')
def status(jobid: str):
    j = get_job(jobid)
    return {'state': j['state'], 'message': j['message'], 'captions': j['captions'], 'has_export': bool(j['output'])}


@app.get('/api/jobs/{jobid}/video')
def get_video(jobid: str):
    j = get_job(jobid)
    return FileResponse(j['source'], media_type='video/mp4')


class TranscribeOptions(BaseModel):
    language: str = Field(default='auto', pattern='^(auto|en|hi)$')
    model: str = Field(default='base', pattern='^(tiny|base)$')


def transcribe_worker(jobid, opts):
    j = get_job(jobid)
    try:
        with PROCESS_LOCK:
            report(jobid, state='processing', message='Extracting audio...')
            wav = WORK / jobid / 'audio.wav'
            run_ffmpeg(['-i', j['source'], '-vn', '-ac', '1', '-ar', '16000', str(wav)])
            report(jobid, message='Loading speech recognition model...')
            from faster_whisper import WhisperModel
            model = WhisperModel(opts.model, device='cpu', compute_type='int8')
            report(jobid, message='Transcribing speech...')
            segments, _ = model.transcribe(str(wav), language=None if opts.language == 'auto' else opts.language,
                                            beam_size=3, vad_filter=True, word_timestamps=True)
            captions = []
            for seg in segments:
                words = seg.words or []
                if words:
                    group = []
                    for word in words:
                        if group and (len(group) >= 5 or word.end - group[0].start > 2.6):
                            captions.append({'start': round(group[0].start, 2), 'end': round(group[-1].end, 2),
                                             'text': ''.join(w.word for w in group).strip()})
                            group = []
                        group.append(word)
                    if group:
                        captions.append({'start': round(group[0].start, 2), 'end': round(group[-1].end, 2),
                                         'text': ''.join(w.word for w in group).strip()})
                elif seg.text.strip():
                    captions.append({'start': round(seg.start, 2), 'end': round(seg.end, 2), 'text': seg.text.strip()})
            report(jobid, captions=captions, state='done', message=f'{len(captions)} captions created')
            wav.unlink(missing_ok=True)
    except Exception as exc:
        report(jobid, state='error', message=str(exc)[:600])


@app.post('/api/jobs/{jobid}/transcribe')
def transcribe(jobid: str, opts: TranscribeOptions):
    j = get_job(jobid)
    if j['state'] in ('processing','exporting'):
        raise HTTPException(409, 'Already processing')
    report(jobid, state='processing', message='Starting AI captions...')
    threading.Thread(target=transcribe_worker, args=(jobid, opts), daemon=True).start()
    return {'started': True}


class Caption(BaseModel):
    start: float = Field(ge=0, le=200000)
    end: float = Field(gt=0, le=200000)
    text: str = Field(max_length=500)


class CaptionPayload(BaseModel):
    captions: list[Caption] = Field(max_length=5000)


def normalized(captions):
    rows = []
    for c in captions:
        if c.end <= c.start: continue
        rows.append({'start': float(c.start), 'end': float(c.end), 'text': c.text.strip()})
    return sorted(rows, key=lambda x: x['start'])


@app.put('/api/jobs/{jobid}/captions')
def save_captions(jobid: str, payload: CaptionPayload):
    get_job(jobid)
    rows = normalized(payload.captions)
    report(jobid, captions=rows)
    return {'saved': len(rows)}


def srt_time(t):
    ms = int(round(max(0,t)*1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


@app.get('/api/jobs/{jobid}/srt')
def get_srt(jobid: str):
    from fastapi.responses import Response
    rows = get_job(jobid)['captions']
    s = ''.join(f'{i}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n\n' for i,c in enumerate(rows,1))
    return Response(s, media_type='text/plain; charset=utf-8', headers={'Content-Disposition': 'attachment; filename="captions.srt"'})


class ExportOptions(CaptionPayload):
    size: int = Field(default=42, ge=14, le=110)
    position: int = Field(default=82, ge=10, le=95)
    color: str = Field(default='#ffffff', pattern='^#[0-9a-fA-F]{6}$')
    outline: bool = True


def ass_time(t):
    cs = round(max(0,t)*100)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'


def ass_escape(s):
    return s.replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\r','').replace('\n','\\N')


def export_worker(jobid, opts):
    try:
        with PROCESS_LOCK:
            report(jobid, message='Rendering high quality video...')
            folder = WORK / jobid
            j = get_job(jobid)
            # ASS renderer handles positions in percentages via per-event override.
            rgb = opts.color.lstrip('#')
            bgr = rgb[4:6] + rgb[2:4] + rgb[:2]
            ass = folder / 'captions.ass'
            hdr = ('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n'
                   'WrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n'
                   'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
                   f'Style: Default,Arial,{opts.size},&H00{bgr},&H00{bgr},&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,{3 if opts.outline else 0},0,5,45,45,0,1\n\n'
                   '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
            with ass.open('w', encoding='utf-8') as f:
                f.write(hdr)
                for c in normalized(opts.captions):
                    f.write(f'Dialogue: 0,{ass_time(c["start"])},{ass_time(c["end"])},Default,,0,0,0,,{{\\an5\\pos(540,{round(opts.position*19.2)})}}{ass_escape(c["text"])}\n')
            output = folder / 'captioned.mp4'
            run_ffmpeg(['-i', j['source'], '-vf', 'ass=captions.ass', '-c:v','libx264','-preset','veryfast',
                        '-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)], cwd=folder)
            report(jobid, state='done', message='Export ready', output=str(output))
    except Exception as exc:
        report(jobid, state='error', message='Video export failed: ' + str(exc)[:600])


@app.post('/api/jobs/{jobid}/export')
def export_video(jobid: str, opts: ExportOptions):
    j = get_job(jobid)
    if j['state'] in ('processing','exporting'):
        raise HTTPException(409, 'Already processing')
    if not opts.captions:
        raise HTTPException(400, 'Add captions first')
    report(jobid, state='exporting', message='Preparing video...', captions=normalized(opts.captions), output=None)
    threading.Thread(target=export_worker, args=(jobid, opts), daemon=True).start()
    return {'started': True}


@app.get('/api/jobs/{jobid}/download')
def download_video(jobid: str):
    output = get_job(jobid)['output']
    if not output or not Path(output).exists():
        raise HTTPException(404, 'Export is not ready')
    return FileResponse(output, media_type='video/mp4', filename='caption-studio-export.mp4')


app.mount('/', StaticFiles(directory=ROOT / 'static', html=True), name='static')
