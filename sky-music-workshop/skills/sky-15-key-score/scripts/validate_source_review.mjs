#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {validateRapidTimeline} from './rapid_timeline.mjs';
import {pathToFileURL} from 'node:url';

const fail=message=>{throw new Error(`Source review: ${message}`);};
const requireThat=(condition,message)=>{if(!condition)fail(message);};
const normalized=notes=>JSON.stringify([...notes].sort());
const validNotes=new Set(['1','2','3','4','5','6','7',"1'","2'","3'","4'","5'","6'","7'","1''"]);

// A separately read source ledger is evidence, not a proof of perfect reading.
// Never generate it by copying the manifest that it is meant to check.
export function validateSourceReview(manifest,base){
  const reviewName=manifest.audit?.source_review;
  requireThat(typeof reviewName==='string'&&reviewName.length,'audit.source_review must name an independently read source ledger; booleans/counts alone cannot release a score');
  const reviewPath=path.resolve(base,reviewName);
  const review=JSON.parse(fs.readFileSync(reviewPath,'utf8'));
  requireThat(review.version===1,'unsupported ledger version');
  requireThat(review.method===(manifest.demo===true?'synthetic_fixture':'independent_source_read'),'ledger method must match real independent reading or declared synthetic demo');
  requireThat(typeof review.review_note==='string'&&review.review_note.trim().length>0,'describe how the second source reading was performed');
  requireThat(Array.isArray(review.unresolved)&&review.unresolved.length===0,'unresolved source questions must be settled before release');
  requireThat(Array.isArray(review.sources)&&review.sources.length>0,'sources[] required');
  const sources=new Set();
  for(const s of review.sources){
    requireThat(typeof s.id==='string'&&!sources.has(s.id),'duplicate/missing source id');
    requireThat(typeof s.path==='string'&&s.path.length,'source path required');
    const sourcePath=path.resolve(path.dirname(reviewPath),s.path);
    requireThat(fs.existsSync(sourcePath)&&fs.statSync(sourcePath).isFile(),`missing source: ${s.id}`);
    sources.add(s.id);
  }
  requireThat(sources.size===manifest.audit.source_page_count,'source page count differs from ledger');
  requireThat(Array.isArray(review.systems)&&review.systems.length>0,'systems[] required');
  const systems=new Map(),expected=new Map(),usedSources=new Set();
  for(const s of review.systems){
    requireThat(typeof s.id==='string'&&!systems.has(s.id),'duplicate/missing system id');
    requireThat(sources.has(s.source_id),`unknown source for ${s.id}`);
    requireThat(Number.isInteger(s.source_row)&&s.source_row>=1,`source row required for ${s.id}`);
    requireThat(Array.isArray(s.events)&&s.events.length>0,`events required for ${s.id}`);
    let prior=-1;
    for(const e of s.events){
      requireThat(typeof e.id==='string'&&!expected.has(e.id),'duplicate/missing source event id');
      requireThat(Number.isInteger(e.time)&&e.time>prior,`invalid event time in ${s.id}`);
      requireThat(Array.isArray(e.notes)&&e.notes.length&&e.notes.every(n=>validNotes.has(n))&&new Set(e.notes).size===e.notes.length,`invalid source notes: ${e.id}`);
      requireThat(typeof e.rapid_to_next==='boolean',`missing rapid relation: ${e.id}`);
      expected.set(e.id,{...e,system:s.id}); prior=e.time;
    }
    systems.set(s.id,s); usedSources.add(s.source_id);
  }
  requireThat(usedSources.size===sources.size,'a source page has no reviewed systems');
  const expectedSystemOrder=[...systems.keys()];let systemOrdinal=0;
  const seen=new Set(),seenSystems=new Set(),actual=new Map();
  const units=manifest.slots_per_measure||8;
  for(const page of manifest.pages){
    for(const s of page.systems){
      requireThat(systems.has(s.source_system_id)&&!seenSystems.has(s.source_system_id),'unknown or reused source system');
      requireThat(s.source_system_id===expectedSystemOrder[systemOrdinal++],`source system order changed: ${s.source_system_id}`);
      seenSystems.add(s.source_system_id);
      for(const [mi,measure] of s.measures.entries())for(const e of measure){
        const ref=e.source_event_id,src=expected.get(ref),time=mi*units+e.slot;
        requireThat(src&&!seen.has(ref),`unknown or reused source event: ${ref}`);
        requireThat(src.system===s.source_system_id,`event moved to another system: ${ref}`);
        requireThat(time===src.time,`time mismatch ${ref}: ${time} != ${src.time}`);
        requireThat(Array.isArray(e.notes)&&normalized(e.notes)===normalized(src.notes),`notes mismatch ${ref}: ${JSON.stringify(e.notes)} != ${JSON.stringify(src.notes)}`);
        requireThat(e.rapid_to_next===src.rapid_to_next,`rapid relation mismatch ${ref}`);
        actual.set(ref,{...e,time}); seen.add(ref);
      }
    }
  }
  requireThat(seen.size===expected.size,'missing reviewed source events');
  requireThat(seenSystems.size===systems.size,'missing reviewed source systems');
  requireThat(Array.isArray(review.regressions),'regressions[] required (empty only if there are no known cases)');
  const regressionIds=new Set(); let assertions=0;
  for(const r of review.regressions){
    requireThat(typeof r.id==='string'&&!regressionIds.has(r.id),'duplicate/missing regression id');
    requireThat(Array.isArray(r.checks)&&r.checks.length>0,`executable checks required: ${r.id}`);
    regressionIds.add(r.id);
    for(const c of r.checks){
      const e=actual.get(c.event_id);
      requireThat(e,`regression references unknown event: ${c.event_id}`);
      requireThat(['notes','time','rapid_to_next'].some(k=>Object.hasOwn(c,k)),`empty assertion: ${r.id}`);
      if(Object.hasOwn(c,'notes'))requireThat(Array.isArray(c.notes)&&normalized(c.notes)===normalized(e.notes),`regression notes failed: ${r.id}`);
      if(Object.hasOwn(c,'time'))requireThat(c.time===e.time,`regression time failed: ${r.id}`);
      if(Object.hasOwn(c,'rapid_to_next'))requireThat(c.rapid_to_next===e.rapid_to_next,`regression rapid relation failed: ${r.id}`);
      assertions++;
    }
  }
  for(const label of manifest.audit.regression_checks||[])requireThat(regressionIds.has(label),`regression label has no executable checks: ${label}`);
  const timeline=validateRapidTimeline(manifest);
  return {timeline,verified_source_pages:sources.size,verified_systems:systems.size,verified_events:seen.size,regressions:regressionIds.size,assertions};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  const file=path.resolve(process.argv[2]||'');
  if(!process.argv[2])throw new Error('Usage: validate_source_review.mjs MANIFEST.json');
  console.log(JSON.stringify(validateSourceReview(JSON.parse(fs.readFileSync(file,'utf8')),path.dirname(file)),null,2));
}
