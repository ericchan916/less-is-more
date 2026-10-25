import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { test } from 'node:test';
import assert from 'node:assert/strict';

// Run the shipped pure function without a browser or runtime dependencies.
const source = readFileSync(new URL('../examples/software/form.js', import.meta.url), 'utf8');
const start = source.indexOf('  function organize(');
const end = source.indexOf('  let initial =', start);
assert.ok(start >= 0 && end > start, 'Locate the shipped organizer before running its behavior checks');
const organize = runInNewContext(source.slice(start, end) + '\norganize;');

test('A single paragraph retains content beyond the title limit', () => {
  const input = '甲'.repeat(81) + '周五提交最终稿。';
  const output = organize(input);
  assert.equal(output.title.length, 80);
  assert.ok(output.outline.includes(input));
  assert.ok(output.actions.includes('周五提交最终稿。'));
});

test('A long opening paragraph and subsequent paragraphs both remain', () => {
  const opening = '关于方案的背景'.repeat(15) + '林汐负责确认素材。';
  const following = '周五提交最终稿。';
  const output = organize(opening + '\n\n' + following);
  assert.ok(output.outline.includes(opening));
  assert.ok(output.outline.includes(following));
  assert.ok(output.actions.includes('林汐负责确认素材。'));
  assert.ok(output.actions.includes(following));
});

test('A short title stays a title while body actions remain intact', () => {
  const output = organize('发布计划\n\n周五由林汐提交最终稿。\n\n保留导出与撤销。');
  assert.equal(output.title, '发布计划');
  assert.ok(output.outline.includes('周五由林汐提交最终稿。'));
  assert.ok(output.actions.includes('保留导出与撤销。'));
});
