"""Decode the finished movie and build an inspection contact sheet."""
import json
import subprocess
from pathlib import Path
from finish_demo import ROOT, WORK, EVIDENCE, FF, metadata, run
from PIL import Image, ImageDraw, ImageFont

final=ROOT/'evidence/quizlab-demo-20261023.mp4'
info=metadata(final)
assert 84.9<=info['duration']<=85.1,info
assert any('1920x1080' in stream and 'h264' in stream for stream in info['streams']),info
assert any('aac' in stream for stream in info['streams']),info
decoded=subprocess.run([FF,'-v','error','-i',str(final),'-f','null','-'],capture_output=True,text=True)
assert decoded.returncode==0 and not decoded.stderr.strip(),decoded.stderr
times=[2,16,30,39,51,58.5,64,71,81]
sheet=Image.new('RGB',(1440,885),'#eaece6')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for i,t in enumerate(times):
    file=WORK/f'inspect-{i:02}.png'
    run(['-ss',t,'-i',final,'-frames:v',1,'-vf','scale=480:270',file])
    frame=Image.open(file).convert('RGB')
    x,y=(i%3)*480,(i//3)*295
    sheet.paste(frame,(x,y))
    ImageDraw.Draw(sheet).text((x+9,y+272),f'{t:04.1f}s',font=font,fill='#2b3931')
sheet.save(EVIDENCE/'contact-sheet.jpg',quality=94)
run(['-ss',5,'-i',final,'-frames:v',1,EVIDENCE/'video-poster.png'])
audio=subprocess.run([FF,'-hide_banner','-i',str(final),'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True,encoding='utf-8',errors='replace')
levels=[x for x in audio.stderr.splitlines() if 'mean_volume:' in x or 'max_volume:' in x]
check={'checkedAt':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'metadata':info,'fullDecode':'PASS (all video and audio frames decoded without error)','audioLevels':levels,'sizeBytes':final.stat().st_size,'contactSheet':'evidence/video-20261023/contact-sheet.jpg'}
(EVIDENCE/'final-check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(check,ensure_ascii=False,indent=2))
