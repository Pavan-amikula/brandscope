/* Execute the browser model code in Node, comparing with sklearn/Python cases. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const engine = require(path.join(root, 'web/ml-engine.js'));
const json = name => JSON.parse(fs.readFileSync(path.join(root, 'web/models', name), 'utf8'));
const model = json('propensity.json');
for (const c of json('parity_cases.json')) {
  assert.ok(Math.abs(engine.predict(model, c.profile).probability - c.probability) < 1e-7, 'Browser/sklearn probability mismatch');
}
const rec = json('recommender.json');
const codes = rec.items.slice(0, 2).map(p => p.code);
const suggestions = engine.recommend(rec, codes);
assert.equal(suggestions.length, 5);
assert.ok(suggestions.every(p => !codes.includes(p.code)));
const knowledge = json('knowledge.json');
assert.equal(engine.retrieve(knowledge, 'quasar nebula extragalactic').abstained, true);
assert.ok(engine.retrieve(knowledge, 'How large is the Swedish sample?').answer.includes('Swedish'));
const rows = engine.parseCSV(fs.readFileSync(path.join(root, 'web/models/synthetic-experiment.csv'), 'utf8'));
const result = engine.analyse(rows);
assert.equal(result.n, 8000);
assert.ok(Math.abs(result.contribution.difference - .2290625) < 1e-9);
assert.ok(result.contribution.lower < 0 && result.contribution.upper > 0);
assert.ok(result.conversion.lower > 0);
assert.throws(() => engine.parseCSV('participant_id,arm,converted,contribution\na,control,1,NaN\n'));
console.log('Browser model parity, recommendations, evidence retrieval and experiment checks passed.');
