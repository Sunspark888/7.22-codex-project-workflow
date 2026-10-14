import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {settings} from '../scripts/settings.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
test('defaults preserve our base layout and cover preference',()=>{
 const c=settings({});assert.deepEqual([c.width,c.height,c.scale],[2160,1080,1]);assert.equal(c.cover.style,'photo');assert.equal(c.cover.width,2048);
});
test('custom canvas contains uniformly and keeps separate cover ratio',()=>{
 const c=settings({presentation:{width:1200,height:1600,palette:'mint',cover:{style:'minimal',width:1080,height:1440}}});
 assert.equal(c.scale,1200/2160);assert.equal(c.height,1600);assert.equal(c.cover.height,1440);
});
test('typos, partial dimensions and unsupported options fail explicitly',()=>{
 for(const p of [{presett:'fullhd'},{width:1920},{palette:'unknown'},{width:0,height:20},{cover:{style:'custom'}},{cover:{height:2000}},{preset:'a4'},{cover:{style:'fresh',layout:'mystery'}}])assert.throws(()=>settings({presentation:p}));
});
test('full build supports different score/cover ratios and reports real dimensions',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'sky-export-'));
 try{
  fs.cpSync(path.join(root,'examples/demo'),dir,{recursive:true,filter:f=>!f.split(path.sep).includes('final')});
  const f=path.join(dir,'manifest.json'),m=JSON.parse(fs.readFileSync(f));
  m.presentation={preset:'fullhd',palette:'mint',cover:{style:'minimal',width:1080,height:1440}};
  fs.writeFileSync(f,JSON.stringify(m));
  let r=spawnSync(process.execPath,[path.join(root,'scripts/build.mjs'),f,'--demo'],{encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);
  let report=JSON.parse(fs.readFileSync(path.join(dir,'final/build-report.json')));
  assert.equal(report.status,'rendered');assert.equal(report.outputs.length,4);
  assert.deepEqual(report.outputs.map(o=>[o.width,o.height]),[[1080,1440],[1920,1080],[3840,2160],[3840,2160]]);
  m.presentation.preset='portrait';m.output_dir='portrait';fs.writeFileSync(f,JSON.stringify(m));
  r=spawnSync(process.execPath,[path.join(root,'scripts/build.mjs'),f,'--demo'],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  report=JSON.parse(fs.readFileSync(path.join(dir,'portrait/build-report.json')));assert.deepEqual([report.outputs[1].width,report.outputs[1].height],[1080,1920]);
  // Real transcription must not silently reuse synthetic evidence.
  delete m.demo;fs.writeFileSync(f,JSON.stringify(m));
  r=spawnSync(process.execPath,[path.join(root,'scripts/build.mjs'),f],{encoding:'utf8'});assert.notEqual(r.status,0);assert.match(r.stderr,/ledger method/);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
