const REPO='https://raw.githubusercontent.com/mrdata355/small-business-banking-data-platform/main/notebooks/databricks/';
const NOTEBOOKS=[
  '00_platform_walkthrough.py',
  '01_lakehouse_tables.py',
  '02_stream_monitoring.py',
  '03_mlflow_models.py',
  '04_contract_genome.py'
];
const files=document.getElementById('files');
const code=document.getElementById('code');
async function openNotebook(name){code.textContent=`Loading ${name}…`;try{const response=await fetch(`${REPO}${name}`,{cache:'no-store'});if(!response.ok)throw new Error(`${response.status} ${response.statusText}`);code.textContent=await response.text();}catch(error){code.textContent=`Source is not on main yet or could not be loaded: ${error.message}\n\nOpen the pull request branch in GitHub while the deployment changes are under review.`;}}
files.innerHTML=NOTEBOOKS.map((name,index)=>`<button data-file="${name}">${String(index+1).padStart(2,'0')} · ${name.replace('.py','')}</button>`).join('');
files.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>openNotebook(button.dataset.file)));
openNotebook(NOTEBOOKS[0]);
