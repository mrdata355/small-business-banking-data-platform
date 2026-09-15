const DATA_API = 'https://ep-summer-recipe-argodi6k.apirest.c-4.us-west-2.aws.neon.tech/banking_demo/rest/v1';
let activeApplication = '';

function fmtTime(value) {
  if (!value) return '';
  return new Date(value).toLocaleString();
}

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
}

async function rpc(name, body = {}) {
  const response = await fetch(`${DATA_API}/rpc/${name}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(text || `${response.status} ${response.statusText}`);
  return text ? JSON.parse(text) : null;
}

function metric(label, value) {
  return `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`;
}

function renderSnapshot(snapshot) {
  const m = snapshot.metrics || {};
  document.getElementById('metrics').innerHTML = [
    metric('Landing objects', m.landing_objects ?? 0),
    metric('Stream arrivals', m.stream_arrivals ?? 0),
    metric('Clean events', m.clean_events ?? 0),
    metric('Quarantine', m.quarantine_events ?? 0),
    metric('Canonical apps', m.canonical_applications ?? 0),
    metric('Duplicates ignored', m.duplicates_ignored ?? 0),
  ].join('');

  const canonical = snapshot.canonical || [];
  document.getElementById('canonicalBody').innerHTML = canonical.length ? canonical.map(r => `
    <tr>
      <td class="mono">${esc(r.application_id)}</td>
      <td>${esc(r.event_version)}</td>
      <td>${esc(r.application_status)}</td>
      <td class="${r.documents_complete ? 'ok' : 'pending'}">${r.documents_complete ? 'complete' : 'pending'}</td>
      <td class="${r.financial_package_complete ? 'ok' : 'pending'}">${r.financial_package_complete ? 'complete' : 'pending'}</td>
      <td class="${r.identity_verification_status === 'VERIFIED' ? 'ok' : 'pending'}">${esc(r.identity_verification_status)}</td>
      <td class="${r.ready_for_underwriting ? 'ok' : 'pending'}">${r.ready_for_underwriting ? 'YES' : 'NO'}</td>
      <td>${esc(fmtTime(r.updated_at))}</td>
    </tr>`).join('') : '<tr><td colspan="8" class="empty">No canonical applications yet.</td></tr>';

  const landing = snapshot.landing || [];
  document.getElementById('landingBody').innerHTML = landing.length ? landing.map(r => `
    <tr>
      <td>${esc(fmtTime(r.received_at))}</td>
      <td class="mono">${esc(r.bucket_name)}</td>
      <td class="mono object" title="${esc(r.object_key)}">${esc(r.object_key)}</td>
      <td>${esc(r.object_type)}</td>
      <td class="mono">${esc(r.payload?.application_id)}</td>
      <td class="mono">${esc(r.payload?.event_id)}</td>
    </tr>`).join('') : '<tr><td colspan="6" class="empty">No landing objects yet.</td></tr>';

  const arrivals = snapshot.arrivals || [];
  document.getElementById('arrivalsBody').innerHTML = arrivals.length ? arrivals.map(r => `
    <tr>
      <td>${esc(fmtTime(r.received_at))}</td>
      <td class="mono">${esc(r.event_id)}</td>
      <td class="mono">${esc(r.application_id)}</td>
      <td>${esc(r.event_type)}</td>
      <td>${esc(r.event_version)}</td>
    </tr>`).join('') : '<tr><td colspan="5" class="empty">No stream arrivals yet.</td></tr>';

  const quarantine = snapshot.quarantine || [];
  document.getElementById('quarantineBody').innerHTML = quarantine.length ? quarantine.map(r => `
    <tr>
      <td>${esc(fmtTime(r.quarantined_at))}</td>
      <td class="mono">${esc(r.event_id)}</td>
      <td class="mono">${esc(r.application_id)}</td>
      <td class="bad">${esc(r.dq_reason)}</td>
    </tr>`).join('') : '<tr><td colspan="4" class="empty">No quarantined records.</td></tr>';

  const audit = snapshot.audit || [];
  document.getElementById('auditBody').innerHTML = audit.length ? audit.map(r => `
    <tr>
      <td>${esc(fmtTime(r.created_at))}</td>
      <td>${esc(r.action)}</td>
      <td class="mono">${esc(r.application_id)}</td>
      <td class="mono">${esc(r.event_id)}</td>
      <td class="${r.outcome === 'MERGED' ? 'ok' : r.outcome === 'QUARANTINED' ? 'bad' : 'pending'}">${esc(r.outcome)}</td>
      <td class="mono object" title="${esc(r.detail?.object_key)}">${esc(r.detail?.object_key)}</td>
    </tr>`).join('') : '<tr><td colspan="6" class="empty">No pipeline audit rows yet.</td></tr>';

  const select = document.getElementById('applicationSelect');
  const previous = activeApplication || select.value;
  select.innerHTML = '<option value="">Select application</option>' + canonical.map(r => `<option value="${esc(r.application_id)}">${esc(r.application_id)} · v${esc(r.event_version)} · ${esc(r.application_status)}</option>`).join('');
  if (canonical.some(r => r.application_id === previous)) {
    select.value = previous;
    activeApplication = previous;
  } else if (canonical[0]) {
    activeApplication = canonical[0].application_id;
    select.value = activeApplication;
  }
  document.getElementById('lastUpdated').textContent = `Snapshot ${fmtTime(snapshot.generated_at)}`;
}

async function refresh() {
  try {
    const snapshot = await rpc('live_dashboard_snapshot');
    renderSnapshot(snapshot);
  } catch (err) {
    document.getElementById('resultBody').textContent = `Refresh failed: ${err.message}`;
  }
}

async function sendAction(action) {
  const needsApp = action !== 'new_application';
  if (needsApp && !activeApplication) {
    document.getElementById('resultBody').textContent = 'Create or select an application first.';
    return;
  }
  const buttons = [...document.querySelectorAll('button[data-action]')];
  buttons.forEach(b => b.disabled = true);
  try {
    const payload = {p_action: action, p_application_id: needsApp ? activeApplication : null};
    const result = await rpc('process_live_event', payload);
    if (result?.application_id) activeApplication = result.application_id;
    document.getElementById('resultBody').textContent = JSON.stringify(result, null, 2);
    await refresh();
  } catch (err) {
    document.getElementById('resultBody').textContent = `Request failed: ${err.message}`;
  } finally {
    buttons.forEach(b => b.disabled = false);
  }
}

document.querySelectorAll('button[data-action]').forEach(button => {
  button.addEventListener('click', () => sendAction(button.dataset.action));
});

document.getElementById('applicationSelect').addEventListener('change', (event) => {
  activeApplication = event.target.value;
});

document.getElementById('refreshButton').addEventListener('click', refresh);

refresh();
setInterval(refresh, 3000);
