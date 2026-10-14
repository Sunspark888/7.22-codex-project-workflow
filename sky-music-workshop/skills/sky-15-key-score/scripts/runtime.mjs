import {createRequire} from 'node:module';
import path from 'node:path';
const require=createRequire(import.meta.url);
export function loadSharp(){
  try{return require('sharp');}catch{}
  const root=process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
  if(root){try{return require(path.join(root,'sharp'));}catch{}}
  throw new Error('Missing sharp. Run npm install in this skill directory (Node.js >=20).');
}

export async function requireScoreFont(){
  const {spawnSync}=await import('node:child_process');
  const r=spawnSync('fc-match',['--format=%{family}','DejaVu Sans'],{encoding:'utf8'});
  if(r.status!==0||!r.stdout.split(',').some(x=>x.trim()==='DejaVu Sans'))throw new Error('DejaVu Sans/fontconfig is required for repeatable score glyphs. Install fonts-dejavu-core and fontconfig (Linux), or configure the same font in your environment.');
}
