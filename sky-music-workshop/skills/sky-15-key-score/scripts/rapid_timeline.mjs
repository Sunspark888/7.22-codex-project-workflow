// Time is musical time, never a post-layout pixel distance.
export function flattenTimeline(manifest) {
  const units=manifest.slots_per_measure??8;
  if(!Number.isInteger(units)||units<1)throw new Error('Timeline: invalid slots_per_measure');
  let offset=0; const result=[],objects=new Set();
  for(const [pi,page] of manifest.pages.entries())for(const [si,system] of page.systems.entries()){
    if(system.measures.length!==4)throw new Error('Timeline: default renderer requires four measures; reflow explicitly instead of silently stretching');
    for(const [mi,measure] of system.measures.entries()){
      let prior=-1;
      for(const e of measure){
        if(objects.has(e))throw new Error('Timeline: shared mutable event; clone every repeated occurrence');
        objects.add(e);
        if(!Number.isInteger(e.slot)||e.slot<0||e.slot>=units||e.slot<=prior)throw new Error('Timeline: invalid or unordered slot');
        prior=e.slot;
        result.push({e,time:offset+mi*units+e.slot,pi,si,mi});
      }
    }
    offset+=system.measures.length*units;
  }
  return result;
}

export function validateRapidTimeline(manifest){
  const all=flattenTimeline(manifest);let links=0,boundaries=0;
  for(let i=0;i<all.length;i++){
    const a=all[i],b=all[i+1],expected=!!b&&b.time-a.time===1;
    if(a.e.rapid_to_next!==expected)throw new Error(
      'Timeline: rapid_to_next mismatch at P'+(a.pi+1)+' row '+(a.si+1)+' measure '+(a.mi+1)+' slot '+a.e.slot+
      '; expected '+expected+'. Recheck source timing; do not patch flags blindly.');
    if(expected){links++;if(a.pi!==b.pi||a.si!==b.si||a.mi!==b.mi)boundaries++;}
  }
  return {events:all.length,rapid_links:links,cross_boundary_links:boundaries};
}

// Return each drawable local portion once. A line/page break clips the chain;
// a barline does not. Singleton portions need a short continuation marker.
export function rapidSegments(laid,global){
  const segments=[];let run=[];
  for(let i=0;i<laid.length;i++){
    const v=laid[i];run.push(v);
    if(v.e.rapid_to_next&&i+1<laid.length)continue;
    const first=run[0],last=run.at(-1);
    const incoming=!!global[first.globalIndex-1]?.e.rapid_to_next;
    const outgoing=!!last.e.rapid_to_next&&!!global[last.globalIndex+1];
    if(run.length>1||incoming||outgoing)segments.push({members:run,incoming,outgoing});
    run=[];
  }
  return segments;
}
