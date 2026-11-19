(function (root) {
  'use strict';
  function initial() {
    return ['Inventory feed', 'Client report export', 'Supplier catalog sync'].map((name, i) => ({id: i, name, state: 'OK', reason: 'Output validated'}));
  }
  function transition(job, action) {
    const reasons = {failure: 'Job reported a failure', missed: 'Expected completion missed', stale: 'Output is stale', success: 'Fresh, nonempty output validated'};
    if (!Object.hasOwn(reasons, action)) throw new Error('Unknown action');
    return {...job, state: action === 'success' ? 'OK' : 'ALERT', reason: reasons[action]};
  }
  const api = {initial, transition};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.WatchdogDemo = api;
})(globalThis);
