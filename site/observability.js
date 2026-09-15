const DATA_API = 'https://ep-summer-recipe-argodi6k.apirest.c-4.us-west-2.aws.neon.tech/banking_demo/rest/v1';
const GITHUB_REPO = 'mrdata355/small-business-banking-data-platform';
const charts = {};

const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
const fmt = (value) => value ? new Date(value).toLocaleString() : '';

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

function setChart(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), config);
}

function metric(label, value) {
  return `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`;
}

function countBy(rows, key) {
  const out = {};
  for (const row of rows || []) out[row[key] ?? 'UNKNOWN'] = (out[row[key] ?? 'UNKNOWN'] || 0) + 1;
  return out;
}

function renderCharts(snapshot) {
  const audit = snapshot.audit_series || [];
  const buckets = [...new Set(audit.map(r => r.bucket))].sort();
  const outcomeNames = ['MERGED', 'DUPLICATE_IGNORED', 'QUARANTINED'];
  const colorMap = {MERGED:'#45c486', DUPLICATE_IGNORED:'#ffd37d', QUARANTINED:'#ff707c'};

  setChart('outcomeTimeline', {
    type: 'line',
    data: {labels: buckets.map(fmt), datasets: outcomeNames.map(name => ({label:name, data:buckets.map(b => Number(audit.find(r => r.bucket===b && r.outcome===name)?.count || 0)), borderColor:colorMap[name], backgroundColor:colorMap[name], tension:.25}))},
    options: {responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false}, plugins:{legend:{labels:{color:'#dbe5f0'}}}, scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}
  });

  const outcomes = snapshot.outcomes || [];
  setChart('outcomeChart', {
    type:'doughnut',
    data:{labels:outcomes.map(x=>x.outcome),datasets:[{data:outcomes.map(x=>Number(x.count)),backgroundColor:outcomes.map(x=>colorMap[x.outcome] || '#79b8ff')}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}}}
  });

  const base = snapshot.platform?.base?.metrics || {};
  const total = Math.max(1, Number(base.stream_arrivals || 0));
  const ready = Number(snapshot.readiness?.ready || 0);
  const apps = Math.max(1, Number(snapshot.readiness?.total || 0));
  const healthy = (snapshot.platform?.health || []).filter(x=>x.status==='HEALTHY').length;
  const healthTotal = Math.max(1, (snapshot.platform?.health || []).length);
  const radarValues = [
    100 * Number(base.clean_events || 0) / total,
    100 * (1 - Number(base.quarantine_events || 0) / total),
    100 * (1 - Number(base.duplicates_ignored || 0) / total),
    100 * ready / apps,
    100 * healthy / healthTotal,
  ].map(x => Math.max(0, Math.min(100, x)));
  setChart('radarChart', {
    type:'radar',
    data:{labels:['Clean throughput','DQ acceptance','Unique delivery','Underwriting readiness','Component health'],datasets:[{label:'Current %',data:radarValues,borderColor:'#79b8ff',backgroundColor:'rgba(121,184,255,.18)',pointBackgroundColor:'#79b8ff'}]},
    options:{responsive:true,maintainAspectRatio:false,scales:{r:{beginAtZero:true,max:100,grid:{color:'#263750'},angleLines:{color:'#263750'},pointLabels:{color:'#cbd5e1'},ticks:{display:false}}},plugins:{legend:{labels:{color:'#dbe5f0'}}}}
  });

  const sentimentCounts = snapshot.sentiment_counts || [];
  const sentimentColors = {POSITIVE:'#45c486',NEUTRAL:'#79b8ff',NEGATIVE:'#ff707c'};
  setChart('sentimentChart', {
    type:'bar',
    data:{labels:sentimentCounts.map(x=>x.sentiment_label),datasets:[{label:'Interactions',data:sentimentCounts.map(x=>Number(x.count)),backgroundColor:sentimentCounts.map(x=>sentimentColors[x.sentiment_label] || '#79b8ff')}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}
  });

  const treasury = [...(snapshot.platform?.treasury || [])].reverse();
  setChart('treasuryChart', {
    type:'line',
    data:{labels:treasury.map(x=>fmt(x.created_at)),datasets:[{label:'Anomaly score',data:treasury.map(x=>Number(x.anomaly_score)),borderColor:'#b99cff',backgroundColor:'#b99cff',pointBackgroundColor:treasury.map(x=>x.risk_flag?'#ff707c':'#45c486'),tension:.2}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8',maxTicksLimit:8}},y:{min:0,max:1,ticks:{color:'#93a3b8'}}}}
  });

  const risks = countBy(snapshot.platform?.predictions || [], 'predicted_risk_band');
  setChart('riskChart', {
    type:'bar',
    data:{labels:['LOW','MEDIUM','HIGH'],datasets:[{label:'Predictions',data:['LOW','MEDIUM','HIGH'].map(k=>risks[k]||0),backgroundColor:['#45c486','#ffd37d','#ff707c']}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}
  });
}

function renderHeatmap(rows) {
  const outcomes = ['MERGED','DUPLICATE_IGNORED','QUARANTINED'];
  const buckets = [...new Set((rows||[]).map(r=>r.bucket))].sort().slice(-12);
  const max = Math.max(1, ...rows.map(r=>Number(r.count||0)));
  let html = '<div></div>' + outcomes.map(x=>`<div><b>${esc(x)}</b></div>`).join('');
  for (const bucket of buckets) {
    html += `<div>${esc(new Date(bucket).toLocaleTimeString())}</div>`;
    for (const outcome of outcomes) {
      const count = Number(rows.find(r=>r.bucket===bucket && r.outcome===outcome)?.count || 0);
      const level = count === 0 ? 0 : Math.max(1, Math.min(4, Math.ceil(4*count/max)));
      html += `<div class="heat-${level}">${count}</div>`;
    }
  }
  document.getElementById('heatmap').innerHTML = html || '<div>No data</div>';
}

function renderTables(snapshot) {
  const health = snapshot.platform?.health || [];
  document.getElementById('healthBody').innerHTML = health.map(x=>`<tr><td>${esc(x.component)}</td><td class="${x.status==='HEALTHY'?'ok':'bad'}">${esc(x.status)}</td><td>${esc(x.processed_count)}</td><td>${esc(x.lag_ms)}</td><td>${esc(fmt(x.last_event_ts))}</td><td>${esc(fmt(x.updated_at))}</td></tr>`).join('') || '<tr><td colspan="6">No health records</td></tr>';

  const q = snapshot.platform?.base?.quarantine || [];
  document.getElementById('quarantineBody').innerHTML = q.map(x=>`<tr><td>${esc(fmt(x.quarantined_at))}</td><td class="mono">${esc(x.application_id)}</td><td class="mono">${esc(x.event_id)}</td><td class="bad">${esc(x.dq_reason)}</td></tr>`).join('') || '<tr><td colspan="4">No quarantined records</td></tr>';

  const deployments = snapshot.deployments || [];
  document.getElementById('deploymentBody').innerHTML = deployments.map(x=>`<tr><td>${esc(fmt(x.created_at))}</td><td>${esc(x.provider)}</td><td>${esc(x.environment)}</td><td class="ok">${esc(x.status)}</td><td class="mono">${esc((x.commit_sha||'').slice(0,10))}</td><td>${x.deployment_url?`<a href="${esc(x.deployment_url)}" target="_blank">open</a>`:''}</td></tr>`).join('') || '<tr><td colspan="6">No deployments</td></tr>';

  const comments = snapshot.comments || [];
  document.getElementById('commentBody').innerHTML = comments.map(x=>`<tr><td>${esc(fmt(x.created_at))}</td><td>${esc(x.component)}</td><td class="${x.severity==='ERROR'?'bad':x.severity==='WARN'?'warn':'ok'}">${esc(x.severity)}</td><td>${esc(x.author)}</td><td>${esc(x.message)}</td></tr>`).join('') || '<tr><td colspan="5">No notes</td></tr>';
}

async function loadGithub() {
  try {
    const [commitsResponse, runsResponse] = await Promise.all([
      fetch(`https://api.github.com/repos/${GITHUB_REPO}/commits?per_page=10`),
      fetch(`https://api.github.com/repos/${GITHUB_REPO}/actions/runs?per_page=10`),
    ]);
    const commits = await commitsResponse.json();
    const runsPayload = await runsResponse.json();
    const runs = runsPayload.workflow_runs || [];
    document.getElementById('commitBody').innerHTML = (Array.isArray(commits)?commits:[]).map(x=>`<tr><td>${esc(fmt(x.commit?.author?.date))}</td><td class="mono"><a href="${esc(x.html_url)}" target="_blank">${esc(x.sha.slice(0,10))}</a></td><td>${esc((x.commit?.message||'').split('\n')[0])}</td><td>${esc(x.commit?.author?.name)}</td></tr>`).join('') || '<tr><td colspan="4">GitHub data unavailable</td></tr>';
    document.getElementById('workflowBody').innerHTML = runs.map(x=>`<tr><td><a href="${esc(x.html_url)}" target="_blank">#${esc(x.run_number)}</a></td><td>${esc(x.status)}</td><td class="${x.conclusion==='success'?'ok':x.conclusion==='failure'?'bad':'warn'}">${esc(x.conclusion||'running')}</td><td class="mono">${esc((x.head_sha||'').slice(0,10))}</td><td>${esc(fmt(x.run_started_at))}</td></tr>`).join('') || '<tr><td colspan="5">No workflow runs</td></tr>';
    document.getElementById('githubTime').textContent = `GitHub refreshed ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    document.getElementById('githubTime').textContent = `GitHub refresh failed: ${err.message}`;
  }
}

async function refresh() {
  try {
    const snapshot = await rpc('observability_snapshot');
    const base = snapshot.platform?.base?.metrics || {};
    const treasury = snapshot.platform?.treasury || [];
    const riskFlags = treasury.filter(x=>x.risk_flag).length;
    document.getElementById('metrics').innerHTML = [
      metric('Landing objects', base.landing_objects||0), metric('Stream arrivals',base.stream_arrivals||0),
      metric('Clean events',base.clean_events||0), metric('Quarantine',base.quarantine_events||0),
      metric('Duplicates ignored',base.duplicates_ignored||0), metric('Canonical apps',base.canonical_applications||0),
      metric('Ready applications',snapshot.readiness?.ready||0), metric('Treasury risk flags',riskFlags),
      metric('Predictions',snapshot.platform?.predictions?.length||0), metric('Interactions',snapshot.sentiment?.length||0),
      metric('Automation runs',snapshot.automation_runs?.length||0), metric('Deployments',snapshot.deployments?.length||0),
    ].join('');
    renderCharts(snapshot);
    renderHeatmap(snapshot.audit_series||[]);
    renderTables(snapshot);
    document.getElementById('snapshotTime').textContent = `Snapshot ${fmt(snapshot.generated_at)}`;
  } catch (err) {
    document.getElementById('snapshotTime').textContent = `Backend error: ${err.message}`;
  }
}

document.getElementById('commentButton').addEventListener('click', async () => {
  const author = document.getElementById('commentAuthor').value.trim();
  const message = document.getElementById('commentMessage').value.trim();
  const severity = document.getElementById('commentSeverity').value;
  if (!author || !message) return;
  try {
    await rpc('add_ops_comment',{p_author:author,p_message:message,p_component:'platform',p_severity:severity});
    document.getElementById('commentMessage').value='';
    await refresh();
  } catch (err) {
    alert(`Comment failed: ${err.message}`);
  }
});

refresh();
loadGithub();
setInterval(refresh,5000);
setInterval(loadGithub,60000);
