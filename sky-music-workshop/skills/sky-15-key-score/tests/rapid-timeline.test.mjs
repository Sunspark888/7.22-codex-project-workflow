import test from 'node:test';
import assert from 'node:assert/strict';
import {validateRapidTimeline,rapidSegments} from '../scripts/rapid_timeline.mjs';
const e=(slot,rapid=false)=>({slot,notes:['3'],rapid_to_next:rapid});
const system=(measures=[[],[],[],[]])=>({measures});
const m=systems=>({slots_per_measure:8,pages:[{systems}]});
test('cross-bar link is required and slow gap stays disconnected',()=>{
 const x=m([system([[e(7,true)],[e(0),e(2)],[],[]])]);
 assert.equal(validateRapidTimeline(x).cross_boundary_links,1);
 x.pages[0].systems[0].measures[0][0].rapid_to_next=false;
 assert.throws(()=>validateRapidTimeline(x),/mismatch/);
});
test('cross-row and cross-page links survive pagination',()=>{
 const a=system([[],[],[],[e(7,true)]]),b=system([[e(0)],[],[],[]]);
 assert.equal(validateRapidTimeline(m([a,b])).cross_boundary_links,1);
 assert.equal(validateRapidTimeline({slots_per_measure:8,pages:[{systems:[a]},{systems:[b]}]}).cross_boundary_links,1);
});
test('empty measures retain elapsed time; final event cannot link',()=>{
 const x=m([system([[e(7) ],[],[e(0)],[]])]);validateRapidTimeline(x);
 x.pages[0].systems[0].measures[2][0].rapid_to_next=true;
 assert.throws(()=>validateRapidTimeline(x),/mismatch/);
});
test('repeated mutable events are rejected',()=>{
 const shared=e(0);assert.throws(()=>validateRapidTimeline(m([system([[shared],[shared],[],[]])])),/shared mutable/);
});
test('same wrong flag in both source records still fails timeline check',()=>{
 assert.throws(()=>validateRapidTimeline(m([system([[e(6),e(7)],[],[],[]])])),/mismatch/);
});
test('dense local chain is one segment despite measure changes',()=>{
 const global=[{e:e(7,true),globalIndex:0,mi:0},{e:e(0,true),globalIndex:1,mi:1},{e:e(1),globalIndex:2,mi:1}];
 const s=rapidSegments(global,global);assert.equal(s.length,1);assert.equal(s[0].members.length,3);
});
test('cross-row singleton gets one marker, long chain gets no duplicate marker',()=>{
 const global=[{e:e(7,true),globalIndex:0},{e:e(0,true),globalIndex:1},{e:e(1),globalIndex:2}];
 assert.equal(rapidSegments(global.slice(0,1),global).length,1);
 const s=rapidSegments(global.slice(1),global);assert.equal(s.length,1);assert.equal(s[0].members.length,2);assert.equal(s[0].incoming,true);
});
