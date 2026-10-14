#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {settings,revision} from './settings.mjs';
import {loadSharp} from './runtime.mjs';
const args=process.argv.slice(2),file=args.shift();
if(!file||args.some(a=>!['--demo','--reuse-cover'].includes(a)))throw new Error('Usage: node scripts/build.mjs MANIFEST.json [--demo] [--reuse-cover]');
if(process.env.SKY_SCORE_PAGES)throw new Error('Full build requires all pages; unset SKY_SCORE_PAGES');
const target=path.resolve(file),base=path.dirname(target),m=JSON.parse(fs.readFileSync(target,'utf8'));
if(m.demo===true&&!args.includes('--demo'))throw new Error('Synthetic example: pass --demo; never use it as real transcription evidence');
if(args.includes('--demo')&&m.demo!==true)throw new Error('--demo applies only to a declared synthetic example');
const config=settings(m),sharp=loadSharp();
const out=process.env.SKY_SCORE_OUTPUT_DIR?path.resolve(process.env.SKY_SCORE_OUTPUT_DIR):path.resolve(base,m.output_dir||'final');
fs.mkdirSync(out,{recursive:true});
const reportPath=path.join(out,'build-report.json');
const report={skill_revision:revision,status:'running',synthetic:m.demo===true,presentation:config,outputs:[],steps:[]};
fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
const dir=path.dirname(fileURLToPath(import.meta.url));
try{
 for(const script of ['render_score.mjs',...(!args.includes('--reuse-cover')?['render_cover.mjs']:[]),'compose_outputs.mjs']){
  const run=spawnSync(process.execPath,[path.join(dir,script),target],{encoding:'utf8'});
  if(run.status!==0)throw new Error(script+': '+(run.stderr||run.error?.message||run.stdout));
  process.stdout.write(run.stdout);report.steps.push(script);
 }
 const safe=String(m.song.title).replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_');
 const expected=[`00_${safe}_封面.png`,...m.pages.map((p,i)=>`${String(i+1).padStart(2,'0')}_${safe}_${p.label||`P${i+1}`}.png`),...Array.from({length:Math.ceil(m.pages.length/4)},(_,g)=>`${90+g}_${safe}_四页合成_${String(g+1).padStart(2,'0')}.png`),`99_${safe}_完整总谱.png`];
 for(const name of expected){const f=path.join(out,name);await sharp(f).stats();const {width,height}=await sharp(f).metadata();report.outputs.push({file:name,width,height});}
 const cover=report.outputs[0];if(cover.width!==config.cover.width||cover.height!==config.cover.height)throw new Error('Reused cover dimensions do not match selected settings');
 report.status='rendered';report.next_action='Inspect rendered pages against source, cover glyphs and source ambiguities before delivery';
}catch(e){report.status='failed';report.error=e.message;process.exitCode=1;console.error(e.message);}
fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
