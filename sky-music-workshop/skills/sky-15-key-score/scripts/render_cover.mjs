#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {loadSharp} from './runtime.mjs';
import {settings} from './settings.mjs';
const sharp=loadSharp(); sharp.cache(false);
const file=process.argv[2];
if(!file)throw new Error('Usage: render_cover.mjs MANIFEST.json');
const base=path.dirname(path.resolve(file)),m=JSON.parse(fs.readFileSync(file,'utf8'));
if(m.schema_version!==2||!m.song?.title)throw new Error('schema_version 2 and song.title required');
const c=settings(m).cover,W=c.width,H=c.height;
const resolve=p=>p?path.resolve(base,p):null;
const out=process.env.SKY_SCORE_OUTPUT_DIR?path.resolve(process.env.SKY_SCORE_OUTPUT_DIR):resolve(m.output_dir||'final');
const art=resolve(m.cover_art);
if(art&&!fs.existsSync(art))throw new Error('missing cover_art: '+art);
if(!art&&!m.demo&&c.style!=='minimal')throw new Error('Provide cover_art matching the selected style, or explicitly choose minimal. Do not silently replace missing art.');
const font=resolve(m.cover_font_file),titleFont=resolve(m.cover_title_font_file)||font;
for(const f of [font,titleFont])if(f&&!fs.existsSync(f))throw new Error('missing font: '+f);
if(/[^\u0000-\u024f]/.test(m.song.title+(m.song.subtitle||'')+(m.song.start_note||''))&&!font)throw new Error('Non-Latin cover text requires cover_font_file and cover_font_family for installed/available font glyphs');
if(font&&!m.cover_font_family)throw new Error('Provide cover_font_family matching cover_font_file (e.g. Noto Sans CJK SC)');
if(m.cover_title_font_file&&!m.cover_title_font_family)throw new Error('Provide cover_title_font_family matching cover_title_font_file');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const pad=Math.round(W*.08),maxW=W-2*pad,scale=Math.min(W,H)/2048;
const center=c.layout==='center',ink=art?'#ffffff':'#20374d';
const layers=[];
if(art)layers.push({input:Buffer.from(`<svg width="${W}" height="${H}"><defs><linearGradient id="g" x2="0" y2="1"><stop stop-color="#07121d" stop-opacity="0.05"/><stop offset="1" stop-color="#07121d" stop-opacity="0.65"/></linearGradient></defs><rect width="${W}" height="${H}" fill="url(#g)"/></svg>`)});
const entries=[[m.song.title,150,titleFont,m.cover_title_font_family||m.cover_font_family||'DejaVu Sans'],[m.song.subtitle,62,font,m.cover_font_family||'DejaVu Sans'],[m.song.start_note,48,font,m.cover_font_family||'DejaVu Sans']].filter(e=>e[0]);
const blocks=[];
for(const [text,size,fontfile,family] of entries){
  let raster=await sharp({text:{text:`<span foreground="${ink}">${esc(text)}</span>`,font:`${family} ${Math.max(16,Math.round(size*scale))}`,...(fontfile?{fontfile}:{}),rgba:true}}).png().toBuffer();
  let meta=await sharp(raster).metadata();
  if(meta.width>maxW){raster=await sharp(raster).resize({width:maxW}).png().toBuffer();meta=await sharp(raster).metadata();}
  blocks.push({raster,width:meta.width,height:meta.height});
}
const gap=Math.max(12,Math.round(35*scale)),total=blocks.reduce((n,b)=>n+b.height,0)+gap*(blocks.length-1);
if(total>H*.7)throw new Error('Cover text is too tall; shorten subtitle or select a larger cover');
let y=Math.round(center?(H-total)/2:H-H*.09-total);
for(const b of blocks){layers.push({input:b.raster,left:center?Math.round((W-b.width)/2):pad,top:y});y+=b.height+gap;}
const background=art?await sharp(art).resize(W,H,{fit:'cover'}).png().toBuffer():await sharp({create:{width:W,height:H,channels:4,background:c.style==='fresh'?'#eaf5e7':'#eef7ff'}}).png().toBuffer();
const result=await sharp(background).composite(layers).png().toBuffer();await sharp(result).stats();
fs.mkdirSync(out,{recursive:true});
const safe=String(m.song.title).replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_');
const dest=path.join(out,`00_${safe}_封面.png`),tmp=dest+'.rendering.png';
try{fs.writeFileSync(tmp,result);await sharp(tmp).stats();fs.renameSync(tmp,dest);}finally{fs.rmSync(tmp,{force:true});}
console.log(dest);
