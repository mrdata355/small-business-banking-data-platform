const DATA_API='https://ep-summer-recipe-argodi6k.apirest.c-4.us-west-2.aws.neon.tech/banking_demo/rest/v1';
const charts={};
let activeApplication='';
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
const fmt=v=>v?new Date(v).toLocaleString():'';
async function rpc(name,body={}){const r=await fetch(`${DATA_API}/rpc/${name}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const t=await r.text();if(!r.ok)throw new Error(t||`${r.status} ${r.statusText}`);return t?JSON.parse(t):null;}
function setChart(id,config){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),config);}
function render(snapshot){
  const apps=snapshot.platform?.base?.canonical||[];
  const sel=document.getElementById('applicationSelect');
  const old=activeApplication||sel.value;
  sel.innerHTML='<option value="">Select application</option>'+apps.map(a=>`<option value="${esc(a.application_id)}">${esc(a.application_id)} · v${esc(a.event_version)} · ${esc(a.application_status)}</option>`).join('');
  if(apps.some(a=>a.application_id===old)){activeApplication=old;sel.value=old;}else if(apps[0]){activeApplication=apps[0].application_id;sel.value=activeApplication;}

  const predictions=snapshot.platform?.predictions||[];
  const riskCounts={LOW:0,MEDIUM:0,HIGH:0};predictions.forEach(p=>riskCounts[p.predicted_risk_band]=(riskCounts[p.predicted_risk_band]||0)+1);
  setChart('riskBands',{type:'doughnut',data:{labels:['LOW','MEDIUM','HIGH'],datasets:[{data:['LOW','MEDIUM','HIGH'].map(x=>riskCounts[x]||0),backgroundColor:['#45c486','#ffd37d','#ff707c']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}}}});
  const timeline=[...predictions].reverse();
  setChart('riskTimeline',{type:'line',data:{labels:timeline.map(p=>fmt(p.scored_at)),datasets:[{label:'Risk probability',data:timeline.map(p=>Number(p.risk_probability)),borderColor:'#79b8ff',backgroundColor:'#79b8ff',tension:.2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8',maxTicksLimit:8}},y:{min:0,max:1,ticks:{color:'#93a3b8'}}}}});
  const treasury=[...(snapshot.platform?.treasury||[])].reverse();
  setChart('treasuryRisk',{type:'line',data:{labels:treasury.map(x=>fmt(x.created_at)),datasets:[{label:'Anomaly score',data:treasury.map(x=>Number(x.anomaly_score)),borderColor:'#b99cff',pointBackgroundColor:treasury.map(x=>x.risk_flag?'#ff707c':'#45c486'),tension:.2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8',maxTicksLimit:8}},y:{min:0,max:1,ticks:{color:'#93a3b8'}}}}});
  const versionCounts={};predictions.forEach(p=>{const k=`${p.model_name} v${p.model_version}`;versionCounts[k]=(versionCounts[k]||0)+1;});
  setChart('modelVersions',{type:'bar',data:{labels:Object.keys(versionCounts),datasets:[{label:'Scores',data:Object.values(versionCounts),backgroundColor:'#45c486'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}});
  document.getElementById('predictionBody').innerHTML=predictions.map(p=>`<tr><td>${esc(fmt(p.scored_at))}</td><td class="mono">${esc(p.application_id)}</td><td>${esc(p.model_name)}</td><td>${esc(p.model_version)}</td><td>${esc(Number(p.risk_probability).toFixed(4))}</td><td class="${String(p.predicted_risk_band).toLowerCase()}">${esc(p.predicted_risk_band)}</td><td class="mono">${esc(JSON.stringify(p.features).slice(0,180))}</td></tr>`).join('')||'<tr><td colspan="7">No predictions yet</td></tr>';
  const runs=(snapshot.automation_runs||[]).filter(r=>String(r.automation_name).includes('model'));
  document.getElementById('runBody').innerHTML=runs.map(r=>`<tr><td>${esc(fmt(r.created_at))}</td><td>${esc(r.automation_name)}</td><td>${esc(r.status)}</td><td>${esc(r.records_processed)}</td><td class="mono">${esc(JSON.stringify(r.detail).slice(0,180))}</td></tr>`).join('')||'<tr><td colspan="5">No scoring runs yet</td></tr>';
}
async function refresh(){try{render(await rpc('observability_snapshot'));}catch(err){document.getElementById('output').textContent=`Refresh failed: ${err.message}`;}}
document.getElementById('applicationSelect').addEventListener('change',e=>activeApplication=e.target.value);
document.getElementById('scoreOne').addEventListener('click',async()=>{if(!activeApplication){document.getElementById('output').textContent='Select an application first.';return;}try{const result=await rpc('score_live_application',{p_application_id:activeApplication});document.getElementById('output').textContent=JSON.stringify(result,null,2);await refresh();}catch(err){document.getElementById('output').textContent=err.message;}});
document.getElementById('scoreSweep').addEventListener('click',async()=>{try{const result=await rpc('run_model_sweep');document.getElementById('output').textContent=JSON.stringify(result,null,2);await refresh();}catch(err){document.getElementById('output').textContent=err.message;}});
document.getElementById('refreshButton').addEventListener('click',refresh);
refresh();setInterval(refresh,5000);
