#!/usr/bin/env python3
"""Render a reviewed edit list and measured score anchors; never infer music here."""
import argparse,bisect,json,subprocess,os,math,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps,ImageEnhance
import numpy as np
from source_credit import score_credit,credit_cover

def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))

def validate(path):
 path=Path(path).resolve();root=path.parent;d=json.loads(path.read_text(encoding='utf-8'));res=lambda p:str((root/p).resolve())
 score_credit(d)
 if not all(shutil.which(x) for x in ('ffmpeg','ffprobe')):raise ValueError('Install ffmpeg and ffprobe')
 if not d.get('pages') or not d.get('segments') or not d.get('anchors'):raise ValueError('pages, segments and anchors cannot be empty')
 for p in [d['cover'],*d['pages']]:
  with Image.open(res(p)) as im:
   im.load()
   if p in d['pages'] and im.size!=(2160,1080):raise ValueError('Score pages must use 2160x1080 anchor coordinates')
 out=Path(res(d['output']))
 if out.exists() and not d.get('overwrite',False):raise ValueError('Output exists; set overwrite only when authorized or choose a new version')
 duration=0.;sources={}
 for seg in d['segments']:
  source=res(seg['path'])
  if source not in sources:sources[source]=probe(source)
  meta=sources[source];v=next((x for x in meta['streams'] if x['codec_type']=='video'),None)
  start,end=seg['start'],seg['end']
  if not all(math.isfinite(x) for x in (start,end)) or not 0<=start<end<=float(meta['format']['duration'])+.04:raise ValueError('Invalid segment bounds')
  crop=seg.get('crop',[0,0,1,1])
  if len(crop)!=4 or not all(math.isfinite(x) for x in crop) or min(crop)<0 or crop[2]<=0 or crop[3]<=0 or crop[0]+crop[2]>1 or crop[1]+crop[3]>1:raise ValueError('crop must be normalized x,y,width,height within source')
  if not v or abs(v['width']*crop[2]/(v['height']*crop[3])-736/512)>.005:raise ValueError('Set segment.crop to a calibrated 736:512 region; see edit-and-cursor.md')
  duration+=end-start
 audio=probe(res(d['audio']));astream=next((x for x in audio['streams'] if x['codec_type']=='audio'),None)
 if not astream or abs(float(astream.get('duration',audio['format']['duration']))-duration)>.1:raise ValueError('Audio must follow the same edit list and duration')
 times=[a['t'] for a in d['anchors']]
 if not all(math.isfinite(t) for t in times) or times[0]!=0 or any(b<=a for a,b in zip(times,times[1:])) or times[-1]>duration:raise ValueError('Anchors must start at 0 and strictly increase within edited duration')
 last=None
 for a in d['anchors']:
  if not isinstance(a['page'],int) or not 0<=a['page']<len(d['pages']) or not isinstance(a['row'],int) or a['row']<0:raise ValueError('Invalid zero-based page/row')
  if not all(math.isfinite(a[k]) for k in ('top','x')) or not 0<=a['x']<=2160 or not 22<=a['top']<=835:raise ValueError('Anchor geometry outside page')
  if last and (a['page'],a['row'])<(last['page'],last['row']):raise ValueError('Backward page/row requires a separate repeated score occurrence')
  if last and (a['page'],a['row'])==(last['page'],last['row']) and (a['x']<last['x'] or a['top']!=last['top']):raise ValueError('Same-row anchors must retain top and nondecreasing x')
  last=a
 if set(a['page'] for a in d['anchors'])!=set(range(len(d['pages']))):raise ValueError('Every page must have anchors in sequential order')
 centers=d.get('key_centers',[[x,y] for y in [88,159,230] for x in [220,294,368,442,516]])
 if len(centers)!=15 or any(len(c)!=2 or not 0<=c[0]<736 or not 0<=c[1]<512 for c in centers):raise ValueError('Exactly 15 centers in 736x512 coordinates required')
 for issue in d.get('known_issues',[]):
  if issue.get('decision')!='deferred' or not all(issue.get(k) for k in ('id','scope','description')):raise ValueError('Invalid accepted known issue')
 for t in d.get('qc_times',[]):
  if not math.isfinite(t) or not 0<=t<duration:raise ValueError('qc_times outside duration')
 return d,res,duration,centers

def cursor_at(anchors,t):
 times=[a['t'] for a in anchors];idx=max(0,bisect.bisect_right(times,t)-1);a=anchors[idx];x=a['x']
 if idx+1<len(anchors):
  b=anchors[idx+1]
  if (b['page'],b['row'])==(a['page'],a['row']) and a.get('motion','linear')!='hold':
   u=max(0,min(1,(t-a['t'])/(b['t']-a['t'])));x+=(b['x']-x)*u
 return {**a,'x':x}

def render(path):
 d,res,duration,centers=validate(path)
 fps=30;pages=d['pages'];anchors=d['anchors'];times=[a['t'] for a in anchors]
 assert times==sorted(times) and len(set(times))==len(times),'anchors must be strictly increasing'
 assert all(0<=a['page']<len(pages) for a in anchors)
 cover=Image.open(res(d['cover'])).convert('RGB');cover.load()
 bg=ImageEnhance.Brightness(ImageOps.fit(cover,(1920,1080)).filter(ImageFilter.GaussianBlur(36))).enhance(.38)
 bg.paste(credit_cover(ImageOps.fit(cover,(530,530)),d,Path(path).resolve().parent),(1343,32))
 bases=[];scores=[];masks=[]
 for p in pages:
  im=Image.open(res(p)).convert('RGB');im.load();im=im.resize((1240,620),Image.Resampling.LANCZOS)
  base=bg.copy();base.paste(im,(20,230));bases.append(base);scores.append(im)
  masks.append(Image.fromarray((np.array(im.convert('L'))<115).astype('uint8')*255).filter(ImageFilter.MaxFilter(5)))
 font=ImageFont.truetype(res(d['key_font']) if d.get('key_font') else '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',25)
 out=Path(res(d['output']));out.parent.mkdir(parents=True,exist_ok=True);silent=out.with_suffix('.silent.mp4');tmp=out.with_suffix('.tmp.mp4')
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-crf',str(d.get('crf',16)),'-preset','fast','-threads','4','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
 color=d.get('cursor_color','#E65B63');fi=0;sc=1240/2160;frame_targets={round(t*fps) for t in d.get('qc_times',[])}
 duration=sum(s['end']-s['start'] for s in d['segments'])
 cumulative=0
 for si,s in enumerate(d['segments']):
  count=round((cumulative+s['end']-s['start'])*fps)-round(cumulative*fps);cumulative+=s['end']-s['start']
  crop=s.get('crop',[0,0,1,1]);crop_filter=f'crop=iw*{crop[2]}:ih*{crop[3]}:iw*{crop[0]}:ih*{crop[1]},'
  dec=subprocess.Popen(['ffmpeg','-v','error','-ss',str(s['start']),'-i',res(s['path']),'-vf',crop_filter+'fps=30,scale=736:512','-frames:v',str(count),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
  for _ in range(count):
   raw=dec.stdout.read(736*512*3);assert len(raw)==736*512*3,(si,fi)
   perf=Image.frombytes('RGB',(736,512),raw);pd=ImageDraw.Draw(perf)
   for ki,(y,x) in enumerate((y,x) for x,y in centers):
    key=ki+1;pd.text((x,y+1),str((key-1)%7+1),font=font,fill='white',anchor='mm',stroke_width=2,stroke_fill='#132034')
    for di in range((key-1)//7):pd.ellipse((x-2,y-20-di*7,x+2,y-16-di*7),fill='white',outline='#132034')
   t=fi/fps;a=cursor_at(anchors,t);x=a['x'];page=a['page']
   frame=bases[page].copy();frame.paste(perf.resize((640,445),Image.Resampling.LANCZOS),(1268,614))
   x=round(20+x*sc);top=230+round((a['top']-22)*sc);bottom=230+round((a['top']+245)*sc)
   draw=ImageDraw.Draw(frame);draw.line((x,top+8,x,bottom),fill=color,width=4);draw.polygon([(x-9,top-10),(x+9,top-10),(x,top+3)],fill=color)
   frame.paste(scores[page],(20,230),masks[page])
   enc.stdin.write(frame.tobytes());fi+=1
  dec.stdout.close()
  if dec.wait()!=0:raise RuntimeError('Source decode failed')
  print(f'segment {si+1}/{len(d["segments"])} complete: {fi/fps:.2f}s',flush=True)
 enc.stdin.close();assert enc.wait()==0
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',res(d['audio']),'-map','0:v','-map','1:a:0','-t',str(fi/fps),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(tmp)],check=True)
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(tmp),'-f','null','-'],check=True)
 p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(tmp)]));assert abs(float(p['format']['duration'])-duration)<.15
 # Inspect encoded frames, including every cut and page/row transition.
 boundaries=[a['t'] for a,b in zip(anchors[1:],anchors) if (a['page'],a['row'])!=(b['page'],b['row'])]
 cumulative=0.;cut_frames=[]
 for seg in d['segments'][:-1]:
  cumulative+=seg['end']-seg['start'];cut_frames.append(round(cumulative*fps))
 targets={0,fi-1,*frame_targets}
 for k in cut_frames:targets.update((max(0,k-1),min(fi-1,k)))
 for t in boundaries:
  k=math.ceil(t*fps-1e-8);targets.update((max(0,k-1),min(fi-1,k)))
 qcdir=out.parent/(out.stem+'_qc');qcdir.mkdir(exist_ok=True);checks=[]
 refs=[np.asarray(im.resize((310,155)),dtype=float) for im in scores]
 for k in sorted(targets):
  dest=qcdir/f'frame_{k:06d}.png'
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(tmp),'-vf',f'select=eq(n\\,{k})','-frames:v','1',str(dest)],check=True)
  with Image.open(dest) as im:
   im.load();observed=np.asarray(im.convert('RGB').crop((20,230,1260,850)).resize((310,155)),dtype=float)
  expected=cursor_at(anchors,k/fps);dist=[float(np.abs(observed-r).mean()) for r in refs];best=min(dist)
  if dist[expected['page']]>best+1.0:raise ValueError(f'Encoded page mismatch at frame {k}')
  checks.append({'frame':k,'time':k/fps,'expected_page':expected['page'],'expected_row':expected['row'],'path':str(dest),'page_distance':dist,'page_identity':'ambiguous_requires_visual_review' if sum(abs(x-best)<=1.0 for x in dist)>1 else 'matched','visual_cursor_audio_review':'pending'})
 v=next(x for x in p['streams'] if x['codec_type']=='video')
 if (v['width'],v['height'])!=(1920,1080) or v['codec_name']!='h264' or v['r_frame_rate']!='30/1' or not any(x['codec_type']=='audio' and x['codec_name']=='aac' for x in p['streams']):raise ValueError('Output stream contract failed')
 os.replace(tmp,out);silent.unlink()
 report={'status':'encoded_pending_visual_audio_review','full_decode':'passed','known_issues':d.get('known_issues',[]),'duration':p['format']['duration'],'frames':fi,'anchors':len(anchors),'page_count':len(pages),'checks':checks,'scope':'page comparison is automated; listen to edit seams and inspect cursor/key alignment before marking final'}
 out.with_suffix('.qc.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))

 print(out,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--validate-only',action='store_true');args=p.parse_args()
 if args.validate_only:
  validate(args.manifest);print('valid')
 else:render(args.manifest)
