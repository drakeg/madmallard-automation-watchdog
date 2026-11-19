const {test} = require('node:test');
const assert = require('node:assert/strict');
const {initial, transition} = require('../web/model.js');
test('failures, missed runs and stale output remain alerts until validated recovery', () => {
  for (const action of ['failure', 'missed', 'stale']) {
    const before = initial()[0];
    const failed = transition(before, action);
    assert.equal(failed.state, 'ALERT');
    assert.equal(before.state, 'OK');
    assert.equal(transition(failed, 'success').state, 'OK');
  }
  assert.throws(() => transition(initial()[0], 'start'));
});
