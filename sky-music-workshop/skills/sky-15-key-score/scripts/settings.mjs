// Canonical musical layout stays 2160 x 1080. Output uses uniform scaling only.
export const revision='1.12.0';
export const palettes={
  default:['#e9f5ff','#fff8f4','#edf4ff'],
  mint:['#edf8ed','#f8fcf0','#e7f3ef'],
  paper:['#faf7ef','#fffdf7','#f1eee7']
};
export const presets={default:[2160,1080],fullhd:[1920,1080],uhd:[3840,2160],portrait:[1080,1920]};
function keys(o,allowed,label){
  if(!o||typeof o!=='object'||Array.isArray(o))throw new Error(label+' must be an object');
  for(const k of Object.keys(o))if(!allowed.includes(k))throw new Error(label+': unknown option '+k);
}
function dimensions(w,h,label){
  if(!Number.isInteger(w)||!Number.isInteger(h)||w<720||h<540||w>4096||h>4096)throw new Error(label+': width 720..4096 and height 540..4096 must be integers');
}
export function settings(m){
  const s=m.presentation??{};
  keys(s,['preset','width','height','palette','cover'],'presentation');
  const preset=s.preset??'default';
  if(!Object.hasOwn(presets,preset))throw new Error('unknown presentation.preset: '+preset);
  if((s.width===undefined)!==(s.height===undefined))throw new Error('provide both presentation.width and height');
  const [width,height]=s.width===undefined?presets[preset]:[s.width,s.height];
  dimensions(width,height,'score');
  const palette=s.palette??'default';
  if(!Object.hasOwn(palettes,palette))throw new Error('unknown presentation.palette: '+palette);
  const c=s.cover??{};
  keys(c,['style','width','height','brief','layout'],'presentation.cover');
  const style=c.style??'photo',layout=c.layout??'cinematic';
  if(!['photo','fresh','illustration','minimal','custom'].includes(style))throw new Error('unknown cover.style: '+style);
  if(!['cinematic','center'].includes(layout))throw new Error('unknown cover.layout: '+layout);
  if(c.brief!==undefined&&typeof c.brief!=='string')throw new Error('cover.brief must be a string');
  if(style==='custom'&&!c.brief?.trim())throw new Error('custom cover requires brief');
  const cw=c.width??m.cover_size??2048,ch=c.height??m.cover_size??2048;
  if((c.width===undefined)!==(c.height===undefined))throw new Error('provide both cover.width and height');
  dimensions(cw,ch,'cover');
  return {width,height,palette,colors:palettes[palette],scale:Math.min(width/2160,height/1080),cover:{style,layout,width:cw,height:ch,brief:c.brief??''}};
}
