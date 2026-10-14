#!/usr/bin/env python3
"""Build PCM audio from the exact reviewed segment list; no silence removal or hidden retiming."""
import argparse,json,subprocess,os
from pathlib import Path

def build(path):
 path=Path(path).resolve();d=json.loads(path.read_text());root=path.parent
 out=(root/d['audio']).resolve()
 if out.suffix.lower()!='.wav':raise ValueError('Use .wav for the intermediate PCM edit track')
 if out.exists() and not d.get('overwrite',False):raise ValueError('Audio exists; choose a version or authorize overwrite')
 command=['ffmpeg','-v','error','-y'];filters=[]
 for i,s in enumerate(d['segments']):
  if not 0<=s['start']<s['end']:raise ValueError('Invalid edit range')
  command+=['-i',str((root/s['path']).resolve())]
  filters.append(f"[{i}:a:0]atrim=start={s['start']}:end={s['end']},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a{i}]")
 filters.append(''.join(f'[a{i}]' for i in range(len(d['segments'])))+f"concat=n={len(d['segments'])}:v=0:a=1[out]")
 out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_name(out.stem+'.rendering.wav')
 subprocess.run(command+['-filter_complex',';'.join(filters),'-map','[out]','-c:a','pcm_s16le',str(tmp)],check=True)
 os.replace(tmp,out);print(out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');build(p.parse_args().manifest)
