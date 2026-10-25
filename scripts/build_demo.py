"""Captioned walkthrough from genuine application screenshots, no fabricated UI."""
from pathlib import Path
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
assets=ROOT/'docs/assets'
W,H,FPS=1280,800,12
def choose_font(size, serif=False):
    candidates = [Path('C:/Windows/Fonts')/('georgia.ttf' if serif else 'segoeui.ttf'),
        Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSerif.ttf' if serif else 'DejaVuSans.ttf')]
    for candidate in candidates:
        if candidate.exists(): return ImageFont.truetype(str(candidate),size)
    return ImageFont.load_default(size=size)
font=choose_font(22)
small=choose_font(16)
titlefont=choose_font(31,serif=True)
scenes=[
 ('v2/overview.jpg',6,'01 / Marketing decision workspace','Connect shopper evidence to a commercial hypothesis and a controlled test.',0,.30),
 ('v2/prediction.jpg',8,'02 / Supervised repurchase model','November top-20% precision: 67.8% forest vs 63.4% RFM. Historical, not causal.',0,.28),
 ('v2/profile-changed.jpg',5,'03 / Actual fitted-model inference','Changing a coherent behavior profile recalculates the probability and model-path drivers.',0,.10),
 ('v2/recommendations.jpg',8,'04 / Learned product factors','SVD hit-rate@5: 27.9% vs 14.4% popularity among eligible novel-product shoppers.',0,.60),
 ('v2/experiment.jpg',8,'05 / Read the contribution outcome','Synthetic example: conversion improves, but the contribution interval crosses zero.',0,.60),
 ('v2/assistant.jpg',8,'06 / Source-backed evidence retrieval','Fitted TF-IDF retrieval returns existing passages and sources; it is not a generative LLM.',0,.50),
 ('v2/campaign.jpg',6,'07 / Commercial assumptions made explicit','Include discounts on baseline purchases, break-even conversion and test sample size.',.10,.60),
 ('v2/evidence.jpg',6,'08 / Auditable evidence and limits','50 Python checks plus browser-engine reference tests. No invented campaign results.',.10,.90),
]
total=sum(s[1] for s in scenes)
writer=imageio.get_writer(assets/'brandscope-demo.mp4',fps=FPS,codec='libx264',quality=8,
    macro_block_size=16,ffmpeg_params=['-pix_fmt','yuv420p','-movflags','+faststart'])
gif_frames=[];story=[];srt=[];elapsed=0

def stamp(sec):
    return f'{int(sec)//3600:02}:{int(sec)//60%60:02}:{int(sec)%60:02},000'

for idx,(filename,duration,title,caption,start,end) in enumerate(scenes):
    src=Image.open(assets/filename).convert('RGB')
    scale=W/src.width
    src=src.resize((W,round(src.height*scale)),Image.Resampling.LANCZOS)
    crop_height=H-148
    max_scroll=max(0,src.height-crop_height)
    srt.append(f'{idx+1}\n{stamp(elapsed)} --> {stamp(elapsed+duration)}\n{title}\n{caption}\n')
    story.append(f'| {elapsed:02d}–{elapsed+duration:02d}s | {title} | {caption} |')
    for frame in range(duration*FPS):
        t=frame/max(duration*FPS-1,1)
        # Gentle vertical pan through the actual full-page screenshot.
        eased=t*t*(3-2*t)
        offset=round(max_scroll*(start+(end-start)*eased))
        canvas=Image.new('RGB',(W,H),'#f6f4ef')
        screenshot=src.crop((0,offset,W,offset+crop_height))
        canvas.paste(screenshot,(0,0))
        draw=ImageDraw.Draw(canvas)
        draw.rectangle((0,crop_height,W,H),fill='#252a2b')
        draw.text((28,crop_height+15),title,font=titlefont,fill='#fff9ee')
        draw.text((29,crop_height+61),caption,font=font,fill='#e4d7d8')
        draw.text((29,H-30),'BrandScope / Independent portfolio case study / Actual captured application states',font=small,fill='#b6b7b0')
        progress=(elapsed+frame/FPS)/total
        draw.rectangle((0,H-4,int(W*progress),H),fill='#b18080')
        writer.append_data(np.asarray(canvas))
        if frame%FPS==0:
            gif_frames.append(canvas.resize((768,480),Image.Resampling.LANCZOS))
        if idx==0 and frame==0:canvas.save(assets/'demo-poster.jpg',quality=94)
    elapsed+=duration
writer.close()
gif_frames[0].save(assets/'brandscope-preview.gif',save_all=True,append_images=gif_frames[1:],duration=1000,loop=0,optimize=True)
(assets/'brandscope-demo.srt').write_text('\n'.join(srt),encoding='utf-8')
(ROOT/'docs/DEMO.md').write_text('''# Demo walkthrough

The 55-second MP4 is a captioned walkthrough assembled from genuine browser screenshots captured while exercising the running Python application. It uses slow vertical pans through full-page captures and successive live-monitor states. It has no audio and is not a continuous desktop recording. No UI or analytical results are fabricated.

The upgraded screenshots show fitted model inference, product recommendations, source retrieval and an explicitly synthetic experiment. The local API and public browser engine share the same model contracts. Observational metrics and commercial scenarios are not measured campaign impact.

| Time | Screen | Explanation |
| --- | --- | --- |
'''+'\n'.join(story)+'''

Files: `assets/brandscope-demo.mp4`, `assets/brandscope-preview.gif`, `assets/brandscope-demo.srt`. Full application screenshots and a mobile capture are in the same assets folder.

To reproduce the workflow interactively: use the README's two-minute tour, run `python server.py`, change the discount, save a scenario, download a brief, then send events from Activation monitor. Actual captures are from 25 October 2026.
''',encoding='utf-8')
print('Video seconds:',total)
print('MP4 bytes:',(assets/'brandscope-demo.mp4').stat().st_size)
print('GIF bytes:',(assets/'brandscope-preview.gif').stat().st_size)
