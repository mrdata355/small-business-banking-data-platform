const DATA_API='https://ep-summer-recipe-argodi6k.apirest.c-4.us-west-2.aws.neon.tech/banking_demo/rest/v1';
let streamTimer=null;
let streamTicks=0;
let selectedApplication='';

const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
const fmt=v=>v?new Date(v).toLocaleString():'';

async function rpc(name,body={}){
  const r=await fetch(`${DATA_API}/rpc/${name}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const t=await r.text();
  if(!r.ok) throw new Error(t||`${r.status} ${r.statusText}`);
  return t?JSON.parse(t):null;
}

async function snapshot(){return rpc('observability_snapshot');}

function show(value){document.getElementById('jobOutput').textContent=JSON.stringify(value,null,2);}

async function refresh(){
  try{
    const s=await snapshot();
    const apps=s.platform?.base?.canonical||[];
    if(!selectedApplication&&apps[0]) selectedApplication=apps[0].application_id;
    document.getElementById('runBody').innerHTML=(s.automation_runs||[]).map(r=>`<tr><td>${esc(fmt(r.created_at))}</td><td>${esc(r.automation_name)}</td><td class="${r.status==='SUCCEEDED'||r.status==='HEALTHY'?'ok':r.status==='WARN'?'warn':'bad'}">${esc(r.status)}</td><td>${esc(r.records_processed)}</td><td class="mono">${esc(JSON.stringify(r.detail||{}).slice(0,180))}</td></tr>`).join('')||'<tr><td colspan="5">No automation runs</td></tr>';
    const audit=s.platform?.base?.audit||[];
    document.getElementById('auditBody').innerHTML=audit.map(r=>`<tr><td>${esc(fmt(r.created_at))}</td><td>${esc(r.action)}</td><td class="mono">${esc(r.application_id)}</td><td class="mono">${esc(r.event_id)}</td><td class="${r.outcome==='MERGED'?'ok':r.outcome==='QUARANTINED'?'bad':'warn'}">${esc(r.outcome)}</td></tr>`).join('')||'<tr><td colspan="5">No audit records</td></tr>';
    return s;
  }catch(err){show({error:err.message});}
}

async function runJob(job){
  const buttons=[...document.querySelectorAll('button[data-job]')];
  buttons.forEach(b=>b.disabled=true);
  try{
    let result;
    if(job==='batch5') result=await rpc('run_ingestion_batch',{p_count:5});
    if(job==='batch25') result=await rpc('run_ingestion_batch',{p_count:25});
    if(job==='treasury') result=await rpc('run_treasury_burst',{p_count:20});
    if(job==='models') result=await rpc('run_model_sweep');
    if(job==='sentinel') result=await rpc('run_ingestion_sentinel');
    if(job==='sentiment'){
      const results=[];
      for(let i=0;i<10;i++) results.push(await rpc('generate_customer_interaction',{p_application_id:selectedApplication||null}));
      result={generated:results.length,results};
    }
    if(job==='duplicate'||job==='invalid'){
      const s=await snapshot();
      const app=selectedApplication||s.platform?.base?.canonical?.[0]?.application_id;
      if(!app) throw new Error('Create an application first.');
      result=await rpc('process_live_event',{p_action:job==='duplicate'?'duplicate_last':'invalid_event',p_application_id:app});
    }
    show(result);
    await refresh();
  }catch(err){show({error:err.message});}
  finally{buttons.forEach(b=>b.disabled=false);}
}

document.querySelectorAll('button[data-job]').forEach(b=>b.addEventListener('click',()=>runJob(b.dataset.job)));

async function streamTick(){
  streamTicks++;
  try{
    const app=await rpc('process_live_event',{p_action:'new_application',p_application_id:null});
    selectedApplication=app.application_id||selectedApplication;
    await rpc('generate_treasury_event',{p_business_id:null});
    if(streamTicks%2===0) await rpc('generate_customer_interaction',{p_application_id:selectedApplication||null});
    if(streamTicks%5===0) await rpc('run_ingestion_sentinel');
    show({continuous_stream:true,tick:streamTicks,last_application:app});
    await refresh();
    if(streamTicks>=60) stopStream();
  }catch(err){show({continuous_stream:true,error:err.message});stopStream();}
}

function startStream(){
  if(streamTimer) return;
  streamTicks=0;
  document.getElementById('streamDot').classList.add('on');
  document.getElementById('streamLabel').textContent='Continuous generator running · 3 second cadence · max 60 ticks';
  document.getElementById('streamStart').disabled=true;
  document.getElementById('streamStop').disabled=false;
  streamTick();
  streamTimer=setInterval(streamTick,3000);
}

function stopStream(){
  if(streamTimer) clearInterval(streamTimer);
  streamTimer=null;
  document.getElementById('streamDot').classList.remove('on');
  document.getElementById('streamLabel').textContent=`Continuous generator stopped after ${streamTicks} ticks`;
  document.getElementById('streamStart').disabled=false;
  document.getElementById('streamStop').disabled=true;
}

document.getElementById('streamStart').addEventListener('click',startStream);
document.getElementById('streamStop').addEventListener('click',stopStream);

refresh();
setInterval(refresh,5000);
