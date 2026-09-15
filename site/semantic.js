const DATA_API='https://ep-summer-recipe-argodi6k.apirest.c-4.us-west-2.aws.neon.tech/banking_demo/rest/v1';
const charts={};
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
async function rpc(name,body={}){const r=await fetch(`${DATA_API}/rpc/${name}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const t=await r.text();if(!r.ok)throw new Error(t||`${r.status} ${r.statusText}`);return t?JSON.parse(t):null;}
function setChart(id,config){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),config);}
function metric(label,value){return `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`;}
function countBy(rows,key){const out={};for(const row of rows||[])out[row[key]??'UNKNOWN']=(out[row[key]??'UNKNOWN']||0)+1;return out;}
async function refresh(){
  try{
    const s=await rpc('observability_snapshot');
    const base=s.platform?.base?.metrics||{};
    const canonical=s.platform?.base?.canonical||[];
    const treasury=s.platform?.treasury||[];
    const totalRequested=canonical.reduce((a,x)=>a+Number(x.requested_amount||0),0);
    const credit=treasury.filter(x=>x.direction==='CREDIT').reduce((a,x)=>a+Number(x.amount||0),0);
    const debit=treasury.filter(x=>x.direction==='DEBIT').reduce((a,x)=>a+Number(x.amount||0),0);
    const sentiment=s.sentiment_counts||[];
    const positive=Number(sentiment.find(x=>x.sentiment_label==='POSITIVE')?.count||0);
    document.getElementById('metrics').innerHTML=[
      metric('Applications',base.canonical_applications||0),
      metric('Ready for underwriting',s.readiness?.ready||0),
      metric('Requested amount',`$${Math.round(totalRequested).toLocaleString()}`),
      metric('ACH credit',`$${Math.round(credit).toLocaleString()}`),
      metric('ACH debit',`$${Math.round(debit).toLocaleString()}`),
      metric('Positive interactions',positive),
      metric('Quarantined',base.quarantine_events||0),
      metric('Duplicates ignored',base.duplicates_ignored||0),
      metric('Predictions',s.platform?.predictions?.length||0),
      metric('Treasury records',treasury.length),
      metric('Automation runs',s.automation_runs?.length||0),
      metric('Deployments',s.deployments?.length||0),
    ].join('');

    const appCounts=countBy(canonical,'application_status');
    setChart('applicationStatus',{type:'bar',data:{labels:Object.keys(appCounts),datasets:[{label:'Applications',data:Object.values(appCounts),backgroundColor:'#79b8ff'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}});
    setChart('readiness',{type:'doughnut',data:{labels:['Ready','Not ready'],datasets:[{data:[Number(s.readiness?.ready||0),Number(s.readiness?.not_ready||0)],backgroundColor:['#45c486','#ffd37d']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}}}});
    setChart('treasuryDirection',{type:'bar',data:{labels:['CREDIT','DEBIT'],datasets:[{label:'Amount',data:[credit,debit],backgroundColor:['#45c486','#b99cff']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}});
    setChart('sentiment',{type:'bar',data:{labels:sentiment.map(x=>x.sentiment_label),datasets:[{label:'Interactions',data:sentiment.map(x=>Number(x.count)),backgroundColor:sentiment.map(x=>x.sentiment_label==='POSITIVE'?'#45c486':x.sentiment_label==='NEGATIVE'?'#ff707c':'#79b8ff')}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#dbe5f0'}}},scales:{x:{ticks:{color:'#93a3b8'}},y:{beginAtZero:true,ticks:{color:'#93a3b8'}}}}});
  }catch(err){document.getElementById('metrics').innerHTML=metric('Backend error',err.message);}
}
refresh();setInterval(refresh,5000);
