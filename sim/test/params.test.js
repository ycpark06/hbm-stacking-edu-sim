import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const params = JSON.parse(readFileSync(new URL('../params.json', import.meta.url), 'utf8'));
const kinds = new Set(['literature', 'assumption', 'design', 'midterm']);
const valueKeys = ['value', 'equipment_value', 'literature_value'];

function checkTree(node, path = 'params') {
  assert.ok(node && typeof node === 'object' && !Array.isArray(node), `${path}: object`);
  const children = Object.entries(node);
  assert.ok(children.length, `${path}: nonempty object`);
  // Containers contain only parameter objects; any scalar marks a parameter leaf.
  if (children.every(([, child]) => child && typeof child === 'object' && !Array.isArray(child))) {
    for (const [key, child] of children) checkTree(child, `${path}.${key}`);
    return;
  }
  const present = valueKeys.filter(key => Object.hasOwn(node, key));
  assert.ok(present.length, `${path}: value or equipment_value/literature_value`);
  for (const key of present) {
    const value = node[key];
    assert.ok((typeof value === 'number' && Number.isFinite(value)) ||
      (typeof value === 'string' && value.trim().length > 0), `${path}.${key}: finite number or nonempty string`);
  }
  assert.ok(typeof node.unit === 'string' && node.unit.trim(), `${path}: unit`);
  assert.ok(kinds.has(node.kind), `${path}: allowed kind`);
  assert.ok(typeof node.source === 'string' && node.source.trim(), `${path}: source`);
  if (node.kind === 'assumption') {
    assert.ok(node.source.replace(/https?:\/\/\S+/g, '').trim().length > 0,
      `${path}: assumption needs a rationale, not only a URL`);
  }
  if (node.range != null) {
    assert.ok(Array.isArray(node.range) && node.range.length === 2 &&
      node.range.every(Number.isFinite) && node.range[0] <= node.range[1], `${path}: ordered numeric range`);
    for (const key of present) {
      assert.ok(typeof node[key] === 'number' && node[key] >= node.range[0] && node[key] <= node.range[1],
        `${path}.${key}: within range`);
    }
  }
}

test('all parameter leaves have values, units, kinds, sources and valid ranges', () => {
  const { _meta, ...parameters } = params;
  checkTree(parameters);
  for (const kind of kinds) assert.ok(_meta.kind_definitions[kind]);
});

test('linked warpage failure criterion retains its cited value and source', () => {
  const criterion = params.judgement.warpage_fail_um;
  const target = criterion.ref.split('.').reduce((node, key) => node[key], params);
  for (const key of ['value', 'unit', 'kind', 'source']) assert.equal(criterion[key], target[key]);
});

test('ramp comparison retains separate equipment and literature provenance', () => {
  const ramp = params.tcncf_process.ramp_rate;
  assert.ok(Number.isFinite(ramp.equipment_value));
  assert.ok(Number.isFinite(ramp.literature_value));
  assert.equal(ramp.literature_kind, 'literature');
  assert.ok(ramp.literature_source.trim());
});
