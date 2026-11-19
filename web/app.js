'use strict';
let jobs = WatchdogDemo.initial();
const list = document.getElementById('jobs');
function render() {
  list.replaceChildren();
  for (const job of jobs) {
    const card = document.createElement('article'); card.className = 'job';
    const title = document.createElement('h3'); title.textContent = job.name;
    const state = document.createElement('span'); state.className = 'badge ' + job.state; state.textContent = job.state;
    const reason = document.createElement('p'); reason.textContent = job.reason;
    const actions = document.createElement('div'); actions.className = 'actions';
    for (const [action, label] of [['failure', 'Simulate failure'], ['missed', 'Miss a run'], ['stale', 'Stale output'], ['success', 'Validate & recover']]) {
      const button = document.createElement('button'); button.textContent = label;
      button.setAttribute('aria-label', label + ': ' + job.name);
      button.addEventListener('click', () => {
        jobs = jobs.map(item => item.id === job.id ? WatchdogDemo.transition(item, action) : item);
        const updated = jobs.find(item => item.id === job.id);
        const message = job.name + ': ' + updated.reason + ' (simulated)';
        document.getElementById('announcement').textContent = message;
        const event = document.createElement('li'); event.textContent = new Date().toLocaleTimeString() + ' — ' + message;
        const events = document.getElementById('events'); events.prepend(event);
        while (events.children.length > 30) events.lastElementChild.remove();
        render();
      });
      actions.append(button);
    }
    card.append(title, state, reason, actions); list.append(card);
  }
  const count = jobs.filter(job => job.state === 'ALERT').length;
  document.getElementById('alerts').textContent = count;
  document.getElementById('healthy').textContent = jobs.length - count;
}
document.getElementById('reset').addEventListener('click', () => {
  jobs = WatchdogDemo.initial(); document.getElementById('events').replaceChildren();
  document.getElementById('announcement').textContent = 'Demo reset. All synthetic outputs are valid.'; render();
});
render();
