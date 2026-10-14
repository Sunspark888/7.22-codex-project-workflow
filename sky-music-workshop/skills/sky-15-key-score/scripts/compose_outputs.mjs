#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {loadSharp} from './runtime.mjs';
import {settings} from './settings.mjs';

const sharp=loadSharp();
sharp.cache(false);
sharp.concurrency(1);
const manifestPath=path.resolve(process.argv[2]||'');
if(!process.argv[2]||!fs.existsSync(manifestPath))throw new Error('Usage: compose_outputs.mjs MANIFEST.json');
const base=path.dirname(manifestPath),m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(!m.song?.title||!Array.isArray(m.pages))throw new Error('manifest requires song.title and pages[]');
if(m.schema_version!==2)throw new Error('manifest.schema_version must be 2');
const resolveFromBase=p=>p?(path.isAbsolute(p)?p:path.resolve(base,p)):null;
const out=process.env.SKY_SCORE_OUTPUT_DIR?path.resolve(process.env.SKY_SCORE_OUTPUT_DIR):resolveFromBase(m.output_dir||'./final');
if(m.canvas?.width!==2160||m.canvas?.height!==1080)throw new Error('canvas must be the fixed 2160x1080 three-system playback-page size');
const config=settings(m),W=config.width,H=config.height;
const safe=String(m.song.title).replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_');
const pagePath=i=>path.join(out,`${String(i+1).padStart(2,'0')}_${safe}_${m.pages[i].label||`P${i+1}`}.png`);
for(let i=0;i<m.pages.length;i++){
  if(!fs.existsSync(pagePath(i)))throw new Error(`missing rendered page: ${pagePath(i)}`);
  try{await sharp(pagePath(i)).stats();const meta=await sharp(pagePath(i)).metadata();if(meta.width!==W||meta.height!==H)throw new Error('page dimensions differ from presentation; rerender all pages');}catch(error){throw new Error(`rendered page is not fully decodable: ${pagePath(i)}\n${error}`);}
}

async function compose(width,height,items,dest){
  const tmp=`${dest}.${process.pid}.rendering.png`;
  let lastError;
  for(let attempt=1;attempt<=3;attempt++){
    try{
      fs.rmSync(tmp,{force:true});
      const buffer=await sharp({create:{width,height,channels:4,background:'#ffffff'}})
        .composite(items).png({compressionLevel:9,adaptiveFiltering:true}).toBuffer();
      await sharp(buffer).stats();
      fs.writeFileSync(tmp,buffer);
      await sharp(tmp).stats();
      fs.renameSync(tmp,dest);
      return;
    }catch(error){lastError=error;fs.rmSync(tmp,{force:true});}
  }
  throw new Error(`failed to write a fully decodable composite PNG after 3 attempts: ${dest}\n${lastError}`);
}
const groupCount=Math.ceil(m.pages.length/4);
for(let g=0;g<groupCount;g++){
  const indices=[g*4,g*4+1,g*4+2,g*4+3];
  const pos=[[0,0],[0,H],[W,0],[W,H]];
  const items=[];
  indices.forEach((idx,j)=>{if(idx<m.pages.length)items.push({input:pagePath(idx),left:pos[j][0],top:pos[j][1]});});
  const dest=path.join(out,`${90+g}_${safe}_四页合成_${String(g+1).padStart(2,'0')}.png`);
  await compose(W*2,H*2,items,dest);
  console.log(dest);
}
const all=[];
for(let g=0;g<groupCount;g++){
  const indices=[g*4,g*4+1,g*4+2,g*4+3];
  const pos=[[0,g*H*2],[0,g*H*2+H],[W,g*H*2],[W,g*H*2+H]];
  indices.forEach((idx,j)=>{if(idx<m.pages.length)all.push({input:pagePath(idx),left:pos[j][0],top:pos[j][1]});});
}
const complete=path.join(out,`99_${safe}_完整总谱.png`);
await compose(W*2,H*2*groupCount,all,complete);
console.log(complete);
