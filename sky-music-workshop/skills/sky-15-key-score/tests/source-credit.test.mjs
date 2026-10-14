import {test} from 'node:test';
import assert from 'node:assert/strict';
import {scoreCredit} from '../scripts/source_credit.mjs';

test('missing or unconfirmed authors stop real score output',()=>{
  for(const score_source of [undefined,{},[],{author:''},{author:'待确认',basis:'screenshot'},{author:'unknown',basis:'screenshot'},{author:'sky荼苏'}]) {
    assert.throws(()=>scoreCredit({score_source}));
  }
});
test('the byline preserves the confirmed score author, separately from the performer',()=>{
  const m={score_source:{author:'sky荼苏',basis:'User identified the source author'},performer:'Sunspark'};
  assert.deepEqual(scoreCredit(m),{author:'sky荼苏',basis:'User identified the source author',text:'by:sky荼苏'});
});
test('invalid multiline and preformatted names cannot corrupt the byline',()=>{
  for(const author of ['by:sky荼苏','A\nB','x'.repeat(81)]) assert.throws(()=>scoreCredit({score_source:{author,basis:'user'}}));
});
