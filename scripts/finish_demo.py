"""Generate the supplied Chinese narration, subtitles, and MP4 deliverables.

The source video is a real browser recording of the public deployment.
Speech is synthesized using zh-CN-XiaoxiaoNeural, not the student's real voice.
"""
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.venv/video-runtime'))
import edge_tts
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
WORK = ROOT / 'output/playwright/quizlab-demo-20261023'
EVIDENCE = ROOT / 'evidence/video-20261023'
WORK.mkdir(parents=True, exist_ok=True)

SECTIONS = [
    (0, 12, '展示网站首页', '大家好，这是我做的学习自测网页，叫知测 QuizLab。它能帮我们在学完知识后，快速检查自己到底掌握了多少。'),
    (12, 27, '展示题库选择', '打开网站，不用注册登录。首页有英语六级、AI 通识和计算机基础三个题库。我选择 AI 通识，直接开始测试。'),
    (27, 47, '展示答题与解析', '每组有八道题。点击选项后，系统会立即判断对错，并给出知识点解析。比如我故意选错一道，错误选项标红，正确答案标绿，很直观。'),
    (47, 67, '展示成绩与错题重练', '做完后，系统自动生成成绩报告，包括得分、正确题数和答题用时。还可以一键重练本轮错题，答对之后更新成绩，不用整套题重新做。'),
    (67, 85, '展示学习记录与结尾', '返回首页，还能看到保存在本机的练习次数和历史正确率。网站用纯前端开发，部署在 GitHub Pages 上，手机和电脑都能打开。以上就是我的 MVP 演示，谢谢大家。'),
]

def run(args):
    proc = subprocess.run([FF, '-hide_banner', '-nostdin', '-y', *map(str,args)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if proc.returncode:
        raise RuntimeError(proc.stderr[-5000:])
    return proc

def metadata(file):
    result = subprocess.run([FF, '-hide_banner', '-i', str(file)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
    if not match:
        raise RuntimeError(result.stderr)
    duration = int(match[1])*3600+int(match[2])*60+float(match[3])
    return {'duration': duration, 'streams': [x.strip() for x in result.stderr.splitlines() if 'Stream #' in x]}

def ts(t, ass=False):
    if ass:
        v = round(t*100)
        return f'{v//360000}:{v//6000%60:02}:{v//100%60:02}.{v%100:02}'
    v = round(t*1000)
    return f'{v//3600000:02}:{v//60000%60:02}:{v//1000%60:02},{v%1000:03}'

async def speech():
    report = []
    cues = []
    for i,(start,end,label,text) in enumerate(SECTIONS):
        mp3 = WORK/f'speech-{i+1}.mp3'
        if not mp3.exists() or mp3.stat().st_size < 1000:
            print(f'Synthesizing section {i+1}: {label}',flush=True)
            voice = edge_tts.Communicate(text, 'zh-CN-XiaoxiaoNeural', rate='+0%', boundary='WordBoundary')
            events = []
            with mp3.open('wb') as file:
                async for chunk in voice.stream():
                    if chunk['type']=='audio': file.write(chunk['data'])
                    elif chunk['type']=='WordBoundary': events.append(chunk)
            (WORK/f'boundaries-{i+1}.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
        duration = metadata(mp3)['duration']
        target = end-start-0.6
        tempo = duration/target
        wav = WORK/f'speech-{i+1}.wav'
        run(['-i',mp3,'-af',f'atempo={tempo:.8f},adelay=300:all=1,apad','-t',end-start,'-ar',48000,'-ac',1,wav])
        report.append({'section':i+1,'start':start,'end':end,'text':text,'voice':'zh-CN-XiaoxiaoNeural','originalDuration':duration,'tempo':tempo})
        # Group full punctuation phrases to keep each subtitle readable.
        phrases = re.findall(r'[^，。！？]+[，。！？]?',text)
        groups=[]
        for phrase in phrases:
            if groups and len(groups[-1])+len(phrase)<=30:
                groups[-1]+=phrase
            else: groups.append(phrase)
        events_file = WORK/f'boundaries-{i+1}.json'
        events = json.loads(events_file.read_text(encoding='utf-8')) if events_file.exists() else []
        # Align caption groups to actual speech boundary timestamps where possible.
        normalize=lambda s: re.sub(r'[^a-z0-9\u4e00-\u9fff]','',s.lower())
        token_chars=[]
        for e in events:
            for character in normalize(e.get('text','')):
                token_chars.append((character,e['offset']/1e7/tempo,e['duration']/1e7/tempo))
        cursor=0
        total=sum(len(x) for x in groups)
        elapsed=0
        for group in groups:
            norm=normalize(group)
            if token_chars and cursor+len(norm)<=len(token_chars):
                a=start+0.3+token_chars[cursor][1]
                last=token_chars[cursor+len(norm)-1]
                b=min(end-0.2,start+0.3+last[1]+last[2]+0.10)
                cursor+=len(norm)
            else:
                a=start+0.3+target*elapsed/total
                b=start+0.3+target*(elapsed+len(group))/total
            cues.append((a,b,group))
            elapsed+=len(group)
    (WORK/'audio-concat.txt').write_text(''.join(f"file 'speech-{i+1}.wav'\n" for i in range(5)),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',WORK/'audio-concat.txt','-c:a','pcm_s16le',WORK/'narration.wav'])
    (EVIDENCE/'narration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    srt='\n\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{text}' for i,(a,b,text) in enumerate(cues))+'\n'
    (ROOT/'evidence/quizlab-demo-20261023.srt').write_text(srt,encoding='utf-8-sig')
    ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Microsoft YaHei,34,&H00F8F7F2,&H00FFFFFF,&H002B3931,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,2,70,70,25,1
Style: Header,Microsoft YaHei,21,&H00F8F7F2,&H00FFFFFF,&H002B3931,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,7,22,22,5,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    ass+='Dialogue: 0,0:00:00.00,0:01:25.00,Header,,0,0,0,,知测 QuizLab  |  https://xiaoluo21.github.io/study-quiz-mvp/\n'
    for a,b,text in cues:
        ass+=f'Dialogue: 0,{ts(a,True)},{ts(b,True)},Caption,,0,0,0,,{text}\n'
    (WORK/'captions.ass').write_text(ass,encoding='utf-8-sig')
    print(json.dumps(report,ensure_ascii=False),flush=True)

def encode():
    log=json.loads((EVIDENCE/'recording.json').read_text(encoding='utf-8'))
    src=Path(log['rawVideo'])
    offset=max(0,log['clipStartOffsetEstimate']-0.12)
    base=['-ss',f'{offset:.3f}','-i',src]
    clean=ROOT/'evidence/quizlab-demo-20261023-clean.mp4'
    run([*base,'-t',85,'-an','-vf','scale=1920:960:flags=lanczos,pad=1920:1080:0:36:color=0xF7F6F2,tpad=stop_mode=clone:stop_duration=0.5','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',clean])
    final=ROOT/'evidence/quizlab-demo-20261023.mp4'
    # Use cwd-relative ASS path to avoid Windows drive-colon filter escaping.
    subprocess.run([FF,'-hide_banner','-nostdin','-y','-i',str(clean),'-i',str(WORK/'narration.wav'),'-vf',"drawbox=x=0:y=0:w=iw:h=36:color=0x2B3931:t=fill,drawbox=x=0:y=996:w=iw:h=84:color=0x2B3931:t=fill,ass=captions.ass",'-map','0:v:0','-map','1:a:0','-t','85','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(final)],cwd=WORK,check=True,stdout=subprocess.DEVNULL,stderr=(WORK/'encode.log').open('w',encoding='utf-8'))
    verify={str(f.relative_to(ROOT)):metadata(f) for f in [src,clean,final,WORK/'narration.wav']}
    verify['render']={'trimOffset':offset,'publicSite':log['url'],'durationTarget':85,'narration':'AI synthesized Chinese voice; user supplied script','subtitles':'Speech timestamp aligned captions','format':'1920x1080 H.264 / AAC'}
    (EVIDENCE/'video-verification.json').write_text(json.dumps(verify,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(verify,ensure_ascii=False,indent=2))

if __name__=='__main__':
    if '--encode-only' not in sys.argv: asyncio.run(speech())
    if '--speech-only' not in sys.argv: encode()
