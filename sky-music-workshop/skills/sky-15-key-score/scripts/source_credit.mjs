// Credit identifies the source score author, not the performer or layout operator.
export function scoreCredit(manifest) {
  const source = manifest.score_source;
  if (!source || typeof source !== 'object' || Array.isArray(source)) {
    throw new Error('score_source.author and score_source.basis are required; ask who created the source score');
  }
  const author = typeof source.author === 'string' ? source.author.trim() : '';
  const basis = typeof source.basis === 'string' ? source.basis.trim() : '';
  if (!author || /^(unknown|tbd|todo|待确认|待填写|未知|作者姓名|原谱作者)$/i.test(author)) {
    throw new Error('Confirm the source score author before rendering; do not guess or use a placeholder');
  }
  if (author.length > 80 || /[\r\n\u0000-\u001f]/.test(author) || /^by\s*:/i.test(author)) {
    throw new Error('score_source.author must contain the author name only, on one line (maximum 80 characters)');
  }
  if (!basis) throw new Error('score_source.basis must record the user confirmation or visible source attribution');
  return {author, basis, text: `by:${author}`};
}
