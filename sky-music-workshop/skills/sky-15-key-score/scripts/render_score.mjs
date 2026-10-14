#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {loadSharp,requireScoreFont} from './runtime.mjs';
import {settings} from './settings.mjs';
import {rapidSegments} from './rapid_timeline.mjs';
import {validateSourceReview} from './validate_source_review.mjs';

await requireScoreFont();
const sharp=loadSharp();
sharp.cache(false);
sharp.concurrency(1);

const manifestPath=path.resolve(process.argv[2]||'');
if(!process.argv[2]||!fs.existsSync(manifestPath))throw new Error('Usage: render_score.mjs MANIFEST.json');
const base=path.dirname(manifestPath);
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(!manifest.song?.title||!Array.isArray(manifest.pages))throw new Error('manifest requires song.title and pages[]');
if(manifest.schema_version!==2)throw new Error('manifest.schema_version must be 2; legacy or screenshot-driven manifests must be audited before final rendering');
if(manifest.canvas?.width!==2160||manifest.canvas?.height!==1080)throw new Error('canvas must be the fixed 2160x1080 three-system playback-page size');
if(manifest.audit?.event_transcription_verified!==true)throw new Error('audit.event_transcription_verified must be true after source-by-source event checking');
if(manifest.audit?.rapid_candidates_verified!==true)throw new Error('audit.rapid_candidates_verified must be true after checking compact, cross-measure, cross-line, and cross-page rapid candidates');
if(!Number.isInteger(manifest.audit?.source_page_count)||manifest.audit.source_page_count<1)throw new Error('audit.source_page_count must be a positive integer; source and output page counts may differ after three-system reflow');
if(!Array.isArray(manifest.audit?.regression_checks))throw new Error('audit.regression_checks[] is required; use [] only when the user has identified no song-specific regression case');
const validNotes=new Set(['1','2','3','4','5','6','7',"1'","2'","3'","4'","5'","6'","7'","1''"]);
manifest.pages.forEach((page,pi)=>{
  if(page.label!==`P${pi+1}`)throw new Error('page.label must be sequential P1, P2, ...');
  if(!Array.isArray(page.systems))throw new Error(`${page.label||`P${pi+1}`} requires systems[]`);
  if(page.systems.length>3)throw new Error(`${page.label||`P${pi+1}`} has ${page.systems.length} systems; maximum is 3. Move system 4+ to the next page before rendering.`);
  if(pi<manifest.pages.length-1&&page.systems.length!==3)throw new Error(`${page.label||`P${pi+1}`} has ${page.systems.length} systems; every non-final page must have exactly 3.`);
  page.systems.forEach((system,si)=>{
    if(!Array.isArray(system.measures))throw new Error(`${page.label||`P${pi+1}`} system ${si+1} requires measures[]`);
    system.measures.forEach((measure,mi)=>{
      if(!Array.isArray(measure))throw new Error(`${page.label||`P${pi+1}`} system ${si+1} measure ${mi+1} must be an event array`);
      let prior=-1;
      measure.forEach((event,ei)=>{
        if(!Number.isInteger(event.slot)||event.slot<0||event.slot>=(manifest.slots_per_measure||8))throw new Error(`${page.label||`P${pi+1}`} system ${si+1} measure ${mi+1} event ${ei+1} has an invalid slot`);
        if(event.slot<=prior)throw new Error(`${page.label||`P${pi+1}`} system ${si+1} measure ${mi+1} event slots must be strictly increasing`);
        prior=event.slot;
        if(!Array.isArray(event.notes)||!event.notes.length||event.notes.some(n=>!validNotes.has(String(n))))throw new Error(`${page.label||`P${pi+1}`} system ${si+1} measure ${mi+1} event ${ei+1} has invalid notes`);
        if(new Set(event.notes.map(String)).size!==event.notes.length)throw new Error(`${page.label||`P${pi+1}`} system ${si+1} measure ${mi+1} event ${ei+1} repeats a note inside one simultaneous press`);
        if(typeof event.rapid_to_next!=='boolean')throw new Error(`${page.label||`P${pi+1}`} system ${si+1} measure ${mi+1} event ${ei+1} must explicitly set rapid_to_next`);
      });
    });
  });
});
const manifestSystemCount=manifest.pages.reduce((total,page)=>total+page.systems.length,0);
const manifestNoteCount=manifest.pages.reduce((total,page)=>total+page.systems.reduce((st,system)=>st+system.measures.reduce((mt,measure)=>mt+measure.reduce((et,event)=>et+event.notes.length,0),0),0),0);
const manifestDotCount=manifest.pages.reduce((total,page)=>total+page.systems.reduce((st,system)=>st+system.measures.reduce((mt,measure)=>mt+measure.reduce((et,event)=>et+event.notes.reduce((nt,note)=>nt+(String(note).match(/'/g)||[]).length,0),0),0),0),0);
if(manifest.audit.source_system_count!==manifestSystemCount)throw new Error(`source/manifest system count mismatch: ${manifest.audit.source_system_count} != ${manifestSystemCount}`);
if(manifest.audit.source_note_count!==manifestNoteCount)throw new Error(`source/manifest note count mismatch: ${manifest.audit.source_note_count} != ${manifestNoteCount}`);
if(manifest.audit.source_dot_count!==manifestDotCount)throw new Error(`source/manifest dot count mismatch: ${manifest.audit.source_dot_count} != ${manifestDotCount}`);
console.log(JSON.stringify({source_review:validateSourceReview(manifest,base)}));
const resolveFromBase=p=>p?(path.isAbsolute(p)?p:path.resolve(base,p)):null;
const out=process.env.SKY_SCORE_OUTPUT_DIR
  ? path.resolve(process.env.SKY_SCORE_OUTPUT_DIR)
  : resolveFromBase(manifest.output_dir||'./final');
fs.mkdirSync(out,{recursive:true});
const W=2160,H=1080;
const config=settings(manifest);
const slotsPerMeasure=manifest.slots_per_measure||8;
const safeTitle=String(manifest.song.title).replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_');
const pageTitle=/[^\u0000-\u024f]/.test(String(manifest.song.title))?'':String(manifest.song.title).toUpperCase();
const bgPath=resolveFromBase(manifest.score_background);
if(bgPath&&!fs.existsSync(bgPath))throw new Error('missing score_background: '+bgPath);
const bg64=bgPath&&fs.existsSync(bgPath)?fs.readFileSync(bgPath).toString('base64'):null;

const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const line=(p,x1,y1,x2,y2,stroke='#526981',width=2,op=1)=>p.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${width}" opacity="${op}" stroke-linecap="round"/>`);
const txt=(p,x,y,s,size=42,fill='#172338',weight=700,anchor='middle',extra='')=>p.push(`<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="DejaVu Sans,Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" ${extra}>${esc(s)}</text>`);
const keyInfo=raw=>{
  const s=String(raw),digit=s[0],dots=(s.match(/'/g)||[]).length;
  let lane=0;
  if(dots===0)lane=Number(digit)<=5?0:1;
  else if(dots===1)lane=Number(digit)<=3?1:2;
  else lane=2;
  return {raw:s,digit,dots,lane,order:dots*7+Number(digit)};
};
const lanesFor=e=>[0,1,2].map(l=>e.notes.map(keyInfo).filter(n=>n.lane===l).sort((a,b)=>a.order-b.order));

const systems=[];
const global=[];
manifest.pages.forEach((page,pi)=>page.systems.forEach((system,si)=>{
  const events=(system.measures||[]).flatMap((measure,mi)=>(measure||[]).map((e,ei)=>{
    if(!Array.isArray(e.notes)||!Number.isInteger(e.slot))throw new Error(`${page.label} system ${si+1} has invalid event`);
    return {e,mi,ei,slot:mi*slotsPerMeasure+e.slot,lanes:lanesFor(e),pi,si};
  })).sort((a,b)=>a.slot-b.slot);
  systems.push({pi,si,events});
  global.push(...events);
}));
global.forEach((v,i)=>{v.globalIndex=i;});

function systemGeometry(count){
  if(count===3)return {tops:[125,440,755],cardH:285,laneGap:82,fontSize:54,baseY:53,underlineBase:70,separatorBase:232};
  if(count===2)return {tops:[250,650],cardH:285,laneGap:82,fontSize:54,baseY:53,underlineBase:70,separatorBase:232};
  if(count===1)return {tops:[440],cardH:285,laneGap:82,fontSize:54,baseY:53,underlineBase:70,separatorBase:232};
  throw new Error(`page requires 1 to 3 systems, received ${count}`);
}

async function writeVerifiedPng(makePipeline,dest){
  const tmp=`${dest}.${process.pid}.rendering.png`;
  let lastError;
  for(let attempt=1;attempt<=3;attempt++){
    try{
      fs.rmSync(tmp,{force:true});
      const buffer=await makePipeline().png({compressionLevel:9,adaptiveFiltering:true}).toBuffer();
      await sharp(buffer).stats();
      fs.writeFileSync(tmp,buffer);
      await sharp(tmp).stats();
      fs.renameSync(tmp,dest);
      return;
    }catch(error){
      lastError=error;
      fs.rmSync(tmp,{force:true});
    }
  }
  throw new Error(`failed to write a fully decodable PNG after 3 attempts: ${dest}\n${lastError}`);
}

function underline(p,members,y,laneGap,underlineBase){
  if(members.length<2)return;
  const lane=Math.max(...members.flatMap(v=>v.e.notes.map(keyInfo).map(n=>n.lane)));
  const uy=y+underlineBase+lane*laneGap;
  line(p,members[0].x-19,uy,members.at(-1).x+19,uy,'#101820',4.5,1);
}

function renderPage(page,pi){
  const background=bg64
    ? `<image href="data:image/png;base64,${bg64}" x="0" y="0" width="${W}" height="${H}" preserveAspectRatio="xMidYMid slice"/><rect width="${W}" height="${H}" fill="#fff" opacity=".38"/>`
    : `<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${config.colors[0]}"/><stop offset=".55" stop-color="${config.colors[1]}"/><stop offset="1" stop-color="${config.colors[2]}"/></linearGradient></defs><rect width="${W}" height="${H}" fill="url(#bg)"/>`;
  const p=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`,background,`<rect x="28" y="24" width="${W-56}" height="${H-48}" rx="34" fill="#fff" opacity=".18" stroke="#fff" stroke-width="2"/>`];
  txt(p,78,84,page.label||`P${pi+1}`,38,'#223751',780,'start');
  if(pageTitle)txt(p,W-80,82,pageTitle,27,'#36506b',650,'end');
  line(p,146,72,W-102,72,'#6e8498',1.5,.45);
  const pageSystems=systems.filter(v=>v.pi===pi);
  const {tops,cardH,laneGap,fontSize,baseY,underlineBase,separatorBase}=systemGeometry(pageSystems.length);
  const left=120,right=W-120,measureW=(right-left)/4,unit=measureW/slotsPerMeasure;

  pageSystems.forEach((sys,localSi)=>{
    const y=tops[localSi];
    p.push(`<rect x="${left}" y="${y-28}" width="${right-left}" height="${cardH}" rx="22" fill="#fff" opacity=".66" stroke="#b9cad8" stroke-width="1.7"/>`);
    for(let bi=0;bi<=4;bi++){
      const bx=left+bi*measureW;
      line(p,bx,y-2,bx,y+separatorBase,'#405a73',bi===0||bi===4?3:2.3,bi===0||bi===4?.88:.66);
    }
    const laid=sys.events.map(v=>{
      const rawX=left+unit/2+v.slot*unit;
      const widest=Math.max(1,...v.lanes.map(notes=>notes.length));
      const estimatedWidth=fontSize*(widest>1?(.62+(widest-1)*.50):.62);
      const measureLeft=left+v.mi*measureW;
      const measureRight=measureLeft+measureW;
      // Compact simultaneous blocks at slot 0/last must remain entirely
      // inside their measure. Shift the whole event so cross-lane notes stay
      // vertically aligned instead of clipping into a separator.
      const minX=measureLeft+estimatedWidth/2+10,maxX=measureRight-estimatedWidth/2-10;
      const x=Math.max(minX,Math.min(maxX,rawX));
      return {...v,x,minX,maxX};
    });
    // C spacing plan: when a chord-like event touches a consecutive rapid
    // event, open the optical boundary by at most 14 px. Each event moves no
    // more than 7 px and remains inside its original measure.
    for(let i=0;i<laid.length-1;i++){
      const a=laid[i],b=laid[i+1];
      if(a.mi===b.mi&&b.e.slot-a.e.slot===1&&a.e.rapid_to_next&&(a.e.notes.length>1||b.e.notes.length>1)){
        a.x=Math.max(a.minX,a.x-7);
        b.x=Math.min(b.maxX,b.x+7);
      }
    }
    laid.forEach(item=>item.lanes.forEach((notes,lane)=>{
      if(!notes.length)return;
      const label=notes.map(n=>n.digit).join(''),yy=y+baseY+lane*laneGap,tight=notes.length>1;
      const charW=fontSize*(tight?.50:.62),start=item.x-(label.length-1)*charW/2;
      if(tight)notes.forEach((n,i)=>txt(p,start+i*charW,yy,n.digit,fontSize,'#111820',720));
      else txt(p,item.x,yy,label,fontSize,'#111820',720);
      notes.forEach((n,i)=>{for(let d=0;d<n.dots;d++)p.push(`<circle cx="${start+i*charW}" cy="${yy-fontSize-5-d*9}" r="3.7" fill="#111820"/>`);});
    }));

    for(const segment of rapidSegments(laid,global)){
      const members=segment.members;
      if(members.length>1)underline(p,members,y,laneGap,underlineBase);
      else {
        const v=members[0],lane=Math.max(...v.e.notes.map(keyInfo).map(n=>n.lane));
        line(p,v.x-23,y+underlineBase+lane*laneGap,v.x+23,y+underlineBase+lane*laneGap,'#101820',4.5,1);
      }
    }
  });
  p.push('</svg>');
  return p.join('');
}

const selectedPages=new Set(
  String(process.env.SKY_SCORE_PAGES||'')
    .split(',')
    .map(v=>Number(v.trim())-1)
    .filter(v=>Number.isInteger(v)&&v>=0&&v<manifest.pages.length)
);
for(let pi=0;pi<manifest.pages.length;pi++){
  if(selectedPages.size&&!selectedPages.has(pi))continue;
  const label=manifest.pages[pi].label||`P${pi+1}`;
  const dest=path.join(out,`${String(pi+1).padStart(2,'0')}_${safeTitle}_${label}.png`);
  const rendered=Buffer.from(renderPage(manifest.pages[pi],pi));
  if(process.env.SKY_SCORE_SAVE_SVG==='1')fs.writeFileSync(dest.replace(/\.png$/,'.svg'),rendered);
  await writeVerifiedPng(()=>sharp(rendered,{density:72}).resize(config.width,config.height,{fit:'contain',background:config.colors[0]}),dest);
  console.log(dest);
}
