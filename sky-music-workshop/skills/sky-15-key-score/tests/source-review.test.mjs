import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {validateSourceReview} from '../scripts/validate_source_review.mjs';

function fixture(){
  const base=fs.mkdtempSync(path.join(os.tmpdir(),'sky-score-test-'));
  const source=Buffer.from('Synthetic fixture, not an audited music source.');
  fs.writeFileSync(path.join(base,'source'),source);
  const events=[
    {id:'opening',time:0,notes:['6','4'],rapid_to_next:false},
    {id:'triple-1',time:2,notes:["3'"],rapid_to_next:true},
    {id:'triple-2',time:3,notes:["3'"],rapid_to_next:true},
    {id:'triple-3',time:4,notes:["3'",'4'],rapid_to_next:false},
    {id:'high-repeat',time:6,notes:["1''",'5','2'],rapid_to_next:false},
  ];
  const review={version:1,method:'independent_source_read',review_note:'Synthetic unit-test ledger',unresolved:[],sources:[{id:'s',path:'source'}],systems:[{id:'s1',source_id:'s',source_row:1,events}],regressions:[{id:'opening-chord',checks:[{event_id:'opening',notes:['6','4']}]}]};
  fs.writeFileSync(path.join(base,'review.json'),JSON.stringify(review));
  const manifest={slots_per_measure:8,audit:{source_page_count:1,source_review:'review.json',regression_checks:['opening-chord']},pages:[{systems:[{source_system_id:'s1',measures:[events.map(e=>({slot:e.time,notes:[...e.notes],rapid_to_next:e.rapid_to_next,source_event_id:e.id})),[],[],[]]}]}]};
  return {base,review,manifest,events:manifest.pages[0].systems[0].measures[0],close:()=>fs.rmSync(base,{recursive:true,force:true})};
}
function check(name,mutate,pattern){test(name,()=>{const f=fixture();try{mutate(f);if(pattern)assert.throws(()=>validateSourceReview(f.manifest,f.base),pattern);else assert.equal(validateSourceReview(f.manifest,f.base).verified_events,5);}finally{f.close();}});}
check('accepts matching independently read event ledger',()=>{});
check('rejects invented opening accompaniment',f=>f.events[0].notes.push('1'),/notes mismatch/);
check('rejects accompaniment shifted inside a rapid group despite unchanged totals',f=>{f.events[1].notes.push('4');f.events[3].notes.pop();},/notes mismatch/);
check('rejects octave loss in an apparently repeated phrase',f=>f.events[4].notes[0]="1'",/notes mismatch/);
check('rejects a note substitution preserving digit/dot totals',f=>f.events[0].notes[0]='7',/notes mismatch/);
check('rejects changed spacing',f=>f.events[3].slot=5,/time mismatch/);
check('rejects a missing rapid continuation',f=>f.events[2].rapid_to_next=false,/rapid relation mismatch/);
check('rejects missing source event',f=>f.events.pop(),/missing reviewed source events/);
check('rejects repeated source ID',f=>f.events[1].source_event_id='opening',/reused source event/);
check('rejects a missing source file',f=>fs.unlinkSync(path.join(f.base,'source')),/missing source/);
check('rejects boolean-only assurance',f=>delete f.manifest.audit.source_review,/booleans\/counts/);
check('rejects regression labels without assertions',f=>f.manifest.audit.regression_checks.push('not-implemented'),/no executable checks/);
check('rejects unresolved source questions',f=>{f.review.unresolved=['unclear source note'];fs.writeFileSync(path.join(f.base,'review.json'),JSON.stringify(f.review));},/unresolved/);
