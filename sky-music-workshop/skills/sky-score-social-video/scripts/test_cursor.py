"""Small self-contained regression: cut + page transition, validation, encoded QC."""
import importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
spec=importlib.util.spec_from_file_location('cursor',Path(__file__).with_name('render_cursor_video.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class CursorTests(unittest.TestCase):
 def test_motion(self):
  a=[dict(t=0,page=0,row=0,top=98,x=100),dict(t=1,page=0,row=0,top=98,x=200),dict(t=2,page=1,row=0,top=98,x=80)]
  self.assertEqual(c.cursor_at(a,.5)['x'],150)
  self.assertEqual(c.cursor_at(a,1.5)['x'],200)
  self.assertEqual(c.cursor_at(a,2)['page'],1)
  a[0]['motion']='hold';self.assertEqual(c.cursor_at(a,.5)['x'],100)
 def test_encoded_cut(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for n in range(2):
    im=Image.new('RGB',(2160,1080),'white');ImageDraw.Draw(im).rectangle((200+500*n,100,400+500*n,400),fill='black');im.save(root/f'p{n}.png')
   Image.new('RGB',(300,200),'navy').save(root/'cover.png')
   subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=736x512:r=30:d=0.6','-f','lavfi','-i','sine=frequency=440:duration=0.6','-c:v','libx264','-c:a','aac','-y',str(root/'source.mp4')],check=True)
   d=dict(score_source=dict(author='Synthetic fixture',basis='Generated test inputs'),cover='cover.png',pages=['p0.png','p1.png'],segments=[dict(path='source.mp4',start=0,end=.2),dict(path='source.mp4',start=.3,end=.5)],audio='audio.wav',anchors=[dict(t=0,page=0,row=0,top=98,x=120),dict(t=.2,page=1,row=0,top=98,x=120)],output='out.mp4')
   mf=root/'project.json';mf.write_text(json.dumps(d))
   subprocess.run(['python',str(Path(__file__).with_name('render_edit_audio.py')),str(mf)],check=True)
   c.validate(mf);c.render(mf)
   report=json.loads((root/'out.qc.json').read_text());self.assertEqual(report['frames'],12);self.assertEqual(len(report['checks']),4)
   with self.assertRaises(ValueError):c.validate(mf)
   d['output']='other.mp4';d['anchors'][1]['t']=0;mf.write_text(json.dumps(d))
   with self.assertRaises(ValueError):c.validate(mf)
if __name__=='__main__':unittest.main()
