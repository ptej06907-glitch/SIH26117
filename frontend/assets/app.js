const $ = id => document.getElementById(id);
let activeWorkspace = null, activeWorkspaceData = null, activeReadOnly = false, uploading = false, assistantDocumentIds = [];
let workspaceMode = 'create', pendingDelete = null;
let mode = 'login', portal = ['user','supervisor','administrator'].includes(location.pathname.split('/').pop()) ? location.pathname.split('/').pop() : 'user', csrf = '', user = null, toastTimer;
async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {credentials:'same-origin', ...options,
    headers:{'Content-Type':'application/json','X-Workbench-Request':'1','X-CSRF-Token':csrf,...options.headers}});
  const data = await response.json();
  if (!response.ok) {
    if(response.status===401 && !path.startsWith('/auth/')) showAuth();
    const message = Array.isArray(data.detail) ? data.detail.map(e => `${e.loc.at(-1)}: ${e.msg}`).join(' · ') : data.detail;
    throw new Error(message || 'Something went wrong. Please try again.');
  }
  return data;
}
function error(id, message) { $(id).textContent = message; $(id).hidden = !message; }
function toast(message) {clearTimeout(toastTimer); $('toast').textContent=message; $('toast').hidden=false; toastTimer=setTimeout(()=>$('toast').hidden=true,4000);}
function setMode(next) {
  if(portal!=='user'&&next==='register')next='login';
  mode=next; const register=mode==='register';
  $('name-field').hidden=!register; $('display-name').required=register; $('password-help').hidden=!register;
  $('auth-title').textContent=register?'Create a User account.':`${portal[0].toUpperCase()+portal.slice(1)} portal`;
  const descriptions={user:'Sign in to your private workspaces.',supervisor:'Sign in with an account assigned by an Administrator. Create new accounts in the User portal first.',administrator:'Manage every workspace and local account role. New accounts are created in the User portal, then assigned here.'};
  $('auth-subtitle').textContent=register?'New accounts begin with standard User access.':descriptions[portal];
  $('auth-submit').textContent=register?'Create account ↗':'Sign in ↗';
  $('password').autocomplete=register?'new-password':'current-password';
  ['login','register'].forEach(tab=>{$(`${tab}-tab`).classList.toggle('active',tab===mode); $(`${tab}-tab`).setAttribute('aria-pressed',String(tab===mode));});
  error('auth-error','');
}
function setPortal(next,updateUrl=true){portal=next;document.body.dataset.portal=portal;document.querySelectorAll('[data-portal]').forEach(button=>button.classList.toggle('active',button.dataset.portal===portal));$('register-tab').hidden=portal!=='user';if(updateUrl)history.replaceState({},'',`/login/${portal}`);setMode('login');}
document.querySelectorAll('[data-portal]').forEach(button=>button.onclick=()=>setPortal(button.dataset.portal));
function showAuth(){window.ARKLanding?.hide();activeWorkspace=null;activeWorkspaceData=null;$('document-list').replaceChildren();$('generation-list').replaceChildren();user=null;csrf='';$('workspace-view').hidden=true;$('auth-view').hidden=false;$('boot').hidden=true;$('workspace-dialog').close();$('delete-dialog').close();$('workspace-grid').replaceChildren();$('detail-name').textContent='';$('detail-description').textContent='';$('profile-name').textContent='';$('profile-username').textContent='';}
async function showWorkspace(data){
  window.ARKLanding?.hide();user=data.user;csrf=data.csrf_token;$('auth-view').hidden=true;$('workspace-view').hidden=false;$('boot').hidden=true;
  $('profile-name').textContent=user.display_name;$('profile-username').textContent=`@${user.username}`;$('profile-role').textContent=user.role;$('avatar').textContent=user.display_name.slice(0,2).toUpperCase();$('account-display').textContent=user.display_name;$('account-username').textContent=`@${user.username} · ${user.role}`;$('account-avatar').textContent=user.display_name.slice(0,2).toUpperCase();$('admin-users').hidden=user.role!=='administrator';
  $('password').value='';await loadWorkspaces();
}
async function loadWorkspaces(){
  activeWorkspace=null;activeWorkspaceData=null;activeReadOnly=false;$('workspace-nav').hidden=true;$('home-button').classList.add('selected');$('topbar-location').textContent=user?.role==='user'?'My workspaces':'Team workspaces';
  $('workspace-list-view').hidden=false;$('workspace-detail').hidden=true;
  try {
    const data=await api('/workspaces'); const grid=$('workspace-grid');grid.replaceChildren();error('workspace-error','');
    const elevated=user.role!=='user';$('workspace-eyebrow').textContent=elevated?'HIERARCHICAL ACCESS':'YOUR PRIVATE WORK';$('workspace-page-title').textContent=elevated?'Team workspaces':'My workspaces';$('workspace-page-subtitle').textContent=user.role==='supervisor'?'Review workspaces across the team. Other users’ records are read-only.':user.role==='administrator'?'Access every workspace and manage local account roles.':'Separate materials, conversations and deliverables by project.';
    $('workspace-count').textContent=data.workspaces.length;$('empty-state').hidden=data.workspaces.length>0;
    for(const item of data.workspaces){
      const card=document.createElement('button');card.className='workspace-card';card.type='button';
      const icon=document.createElement('span');icon.className='folder';icon.textContent='▱';icon.setAttribute('aria-hidden','true');
      const title=document.createElement('h2');title.textContent=item.name;
      const description=document.createElement('p');description.textContent=item.description||'A private space for your project.';
      const date=document.createElement('small');date.textContent=`Created ${new Date(item.created_at*1000).toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'})} · ${elevated?`Owner: ${item.owner_name}`:'Private'}`;
      card.append(icon,title,description,date);card.addEventListener('click',()=>openWorkspace(item.id));grid.append(card);
    }
  } catch(e){error('workspace-error',e.message);}
}
async function openWorkspace(id){$('document-list').replaceChildren();$('generation-list').replaceChildren();error('generation-error','');$('generation-status').textContent='';try{const item=await api(`/workspaces/${id}`);activeWorkspaceData=item;activeReadOnly=user.role==='supervisor'&&item.owner_id!==user.id;$('detail-name').textContent=item.name;$('detail-description').textContent=item.description||'Personal project workspace.';$('topbar-location').textContent=item.name;$('access-banner').hidden=item.owner_id===user.id;$('access-banner').textContent=activeReadOnly?`Supervisor review access · Owned by ${item.owner_name} (@${item.owner_username}) · Changes are disabled`:`Administrator access · Owned by ${item.owner_name} (@${item.owner_username})`;$('workspace-list-view').hidden=true;$('workspace-detail').hidden=false;$('workspace-nav').hidden=false;$('home-button').classList.remove('selected');activeWorkspace=id;showTab('overview');applyWorkspaceAccess();error('upload-error','');$('upload-status').textContent='';await Promise.all([loadDocuments(id),loadGenerations(id),loadModels(),loadRuns(id),loadReviewQueue()]);}catch(e){error('workspace-error',e.message);}}
function reviewStatusText(status){return {pending_analysis:'Supervisor yet to analyse',pending_approval:'Supervisor yet to approve',approved:'Approved by supervisor',disapproved:'Disapproved - needs revision'}[status]||status;}
async function loadReviewQueue(){
  if(!user)return;try{const data=await api('/review-requests');const list=$('review-queue-list');list.replaceChildren();$('review-queue-title').textContent=user.role==='supervisor'?'Supervisor review queue':'Incident review status';$('review-queue-subtitle').textContent=user.role==='supervisor'?'Review AI findings, then approve or disapprove each incident report.':'Track the Supervisor decision on your submitted incident reports.';
    if(!data.requests.length){list.innerHTML='<p class="empty-copy">No incident review requests yet. Start an inspection review from an incident report.</p>';return;}
    for(const item of data.requests){const card=document.createElement('article');card.className='review-request-card';const header=document.createElement('div');header.className='review-request-header';const title=document.createElement('div');const name=document.createElement('strong');name.textContent=item.filename;const meta=document.createElement('small');meta.textContent=`${item.workspace_name} · ${item.requester_name} · ${new Date(item.created_at*1000).toLocaleString()}`;title.append(name,meta);const badge=document.createElement('span');badge.className=`review-status ${item.status}`;badge.textContent=reviewStatusText(item.status);header.append(title,badge);card.append(header);
      const summary=document.createElement('p');summary.className='review-summary';summary.textContent=item.summary||'AI analysis is available in the workflow history.';card.append(summary);
      const steps=document.createElement('div');steps.className='review-steps';const stepTitle=document.createElement('strong');stepTitle.textContent='AI processing steps';steps.append(stepTitle);const events=item.events||[];if(!events.length){const empty=document.createElement('span');empty.textContent=' Awaiting workflow events.';steps.append(empty);}else{const ol=document.createElement('ol');events.slice(-6).forEach(event=>{const li=document.createElement('li');li.textContent=event.message;ol.append(li);});steps.append(ol);}card.append(steps);
      if(item.reviewer_note){const note=document.createElement('p');note.className='review-note';note.textContent=`Supervisor note: ${item.reviewer_note}`;card.append(note);}
      if(user.role!=='user'){const actions=document.createElement('div');actions.className='review-actions';if(item.status==='pending_analysis'){const analyse=document.createElement('button');analyse.type='button';analyse.className='primary';analyse.textContent='Mark analysed';analyse.onclick=()=>updateReview(item.id,'analyse');actions.append(analyse);}if(item.status==='pending_approval'){const approve=document.createElement('button');approve.type='button';approve.className='primary';approve.textContent='Approve AI processing';approve.onclick=()=>updateReview(item.id,'approve');const reject=document.createElement('button');reject.type='button';reject.className='danger-button';reject.textContent='Disapprove / return';reject.onclick=()=>updateReview(item.id,'disapprove');actions.append(approve,reject);}if(actions.children.length)card.append(actions);}list.append(card);}
  }catch(e){$('review-queue-list').innerHTML=`<p class="error">${e.message}</p>`;}
}
async function updateReview(id,action){const note=action==='disapprove'?window.prompt('Reason for returning this report to the user:','Please address the following before resubmission:')||'Returned for clarification.':window.prompt(action==='analyse'?'Supervisor analysis note (optional):':'Approval note (optional):','')||'';try{await api(`/review-requests/${id}`,{method:'PATCH',body:JSON.stringify({action,note})});toast(action==='approve'?'Incident report approved.':action==='disapprove'?'Incident report returned for revision.':'Analysis recorded; approval is now pending.');await loadReviewQueue();}catch(e){toast(e.message);}}
$('review-queue-refresh').onclick=loadReviewQueue;
function applyWorkspaceAccess(){$('workspace-actions').hidden=activeReadOnly;$('material-files').disabled=activeReadOnly;$('reference-files').disabled=activeReadOnly||user.role!=='administrator';$('assistant-files').disabled=activeReadOnly;$('read-all').disabled=activeReadOnly;$('use-documents').disabled=activeReadOnly;$('task-prompt').disabled=activeReadOnly;$('generate-button').disabled=activeReadOnly;$('run-code').disabled=activeReadOnly;$('drop-zone').classList.toggle('disabled',activeReadOnly);$('reference-drop-zone').classList.toggle('disabled',activeReadOnly||user.role!=='administrator');$('assistant-drop-zone').classList.toggle('disabled',activeReadOnly);$('assistant-review-pack').disabled=activeReadOnly||!assistantDocumentIds.length;}
function showTab(name){document.querySelectorAll('[data-panel]').forEach(panel=>panel.hidden=panel.dataset.panel!==name);document.querySelectorAll('[data-tab]').forEach(button=>button.classList.toggle('active',button.dataset.tab===name));document.querySelectorAll('.workspace-nav-item').forEach(button=>button.classList.toggle('selected',button.dataset.tab===name));if(name==='security')loadNetwork();window.scrollTo({top:0,behavior:'smooth'});}
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>showTab(button.dataset.tab)));
function newWorkspace(){workspaceMode='create';$('workspace-form').reset();$('workspace-dialog-eyebrow').textContent='NEW PROJECT SPACE';$('workspace-dialog-title').textContent='New workspace';$('workspace-dialog-copy').textContent='Keep one project’s materials, answers and deliverables together.';$('create-submit').textContent='Create workspace';error('create-error','');$('workspace-dialog').showModal();$('workspace-name').focus();}
function editWorkspace(){if(!activeWorkspaceData||activeReadOnly)return;workspaceMode='edit';$('workspace-name').value=activeWorkspaceData.name;$('workspace-description').value=activeWorkspaceData.description||'';$('workspace-dialog-eyebrow').textContent='WORKSPACE SETTINGS';$('workspace-dialog-title').textContent='Edit workspace details';$('workspace-dialog-copy').textContent='Update the name and description shown to people with access.';$('create-submit').textContent='Save changes';error('create-error','');$('workspace-dialog').showModal();$('workspace-name').focus();}
$('login-tab').onclick=()=>setMode('login');$('register-tab').onclick=()=>setMode('register');
$('show-password').onclick=()=>{const show=$('password').type==='password';$('password').type=show?'text':'password';$('show-password').textContent=show?'Hide':'Show';$('show-password').setAttribute('aria-label',show?'Hide password':'Show password');};
$('auth-form').onsubmit=async event=>{
  event.preventDefault();error('auth-error','');$('auth-submit').disabled=true;
  const payload={username:$('username').value.trim(),password:$('password').value};if(mode==='register')payload.display_name=$('display-name').value.trim();else payload.portal=portal;
  try{await showWorkspace(await api(`/auth/${mode}`,{method:'POST',body:JSON.stringify(payload)}));}
  catch(e){error('auth-error',e.message);}finally{$('auth-submit').disabled=false;}
};
$('logout').onclick=async()=>{try{await api('/auth/logout',{method:'POST'});showAuth();setMode('login');toast('You have signed out.');}catch(e){toast(e.message);}};
$('new-workspace').onclick=newWorkspace;$('first-workspace').onclick=newWorkspace;
$('close-dialog').onclick=()=>$('workspace-dialog').close();$('cancel-dialog').onclick=()=>$('workspace-dialog').close();
$('rename-workspace').onclick=editWorkspace;
$('delete-workspace').onclick=()=>openDelete({kind:'workspace',id:activeWorkspace,name:activeWorkspaceData?.name||'this workspace'});
$('close-delete').onclick=()=>$('delete-dialog').close();$('cancel-delete').onclick=()=>$('delete-dialog').close();
$('delete-name').addEventListener('input',updateDeleteButton);
$('confirm-delete').onclick=confirmDelete;
$('guide-button').onclick=()=>$('guide-dialog').showModal();$('close-guide').onclick=()=>$('guide-dialog').close();$('guide-start').onclick=()=>$('guide-dialog').close();
$('account-button').onclick=()=>$('account-dialog').showModal();$('close-account').onclick=()=>$('account-dialog').close();$('account-done').onclick=()=>$('account-dialog').close();$('account-logout').onclick=()=>{$('account-dialog').close();$('logout').click();};
$('compact-mode').checked=localStorage.getItem('aegis-compact')==='1';document.body.classList.toggle('compact',$('compact-mode').checked);$('compact-mode').onchange=()=>{document.body.classList.toggle('compact',$('compact-mode').checked);localStorage.setItem('aegis-compact',$('compact-mode').checked?'1':'0');};
$('admin-users').onclick=async()=>{$('users-dialog').showModal();await loadUsers();};$('close-users').onclick=()=>$('users-dialog').close();
async function loadUsers(){error('users-error','');const list=$('users-list');list.innerHTML='<p class="muted">Loading local accounts…</p>';try{const data=await api('/admin/users');list.replaceChildren();for(const account of data.users){const row=document.createElement('div');row.className='user-row';const avatar=document.createElement('span');avatar.className='avatar';avatar.textContent=account.display_name.slice(0,2).toUpperCase();const details=document.createElement('div');const name=document.createElement('strong');name.textContent=account.display_name;const meta=document.createElement('small');meta.textContent=`@${account.username} · ${account.workspace_count} workspaces`;details.append(name,meta);const select=document.createElement('select');select.setAttribute('aria-label',`Role for ${account.display_name}`);for(const role of ['user','supervisor','administrator']){const option=document.createElement('option');option.value=role;option.textContent=role[0].toUpperCase()+role.slice(1);option.selected=role===account.role;select.append(option);}select.disabled=account.id===user.id;select.onchange=async()=>{select.disabled=true;try{await api(`/admin/users/${account.id}/role`,{method:'PATCH',body:JSON.stringify({role:select.value})});toast(`${account.display_name} now uses the ${select.value} portal.`);}catch(e){error('users-error',e.message);select.value=account.role;}finally{select.disabled=account.id===user.id;}};row.append(avatar,details,select);list.append(row);}}catch(e){list.replaceChildren();error('users-error',e.message);}}
$('home-button').onclick=loadWorkspaces;$('back-workspaces').onclick=loadWorkspaces;
$('workspace-form').onsubmit=async event=>{
  event.preventDefault();error('create-error','');$('create-submit').disabled=true;
  const payload=JSON.stringify({name:$('workspace-name').value.trim(),description:$('workspace-description').value.trim()});
  try{if(workspaceMode==='edit'){const item=await api(`/workspaces/${activeWorkspace}`,{method:'PATCH',body:payload});activeWorkspaceData=item;$('detail-name').textContent=item.name;$('detail-description').textContent=item.description||'Personal project workspace.';$('topbar-location').textContent=item.name;$('workspace-dialog').close();toast('Workspace details updated.');}else{await api('/workspaces',{method:'POST',body:payload});$('workspace-dialog').close();await loadWorkspaces();toast('Workspace created.');}}
  catch(e){error('create-error',e.message);}finally{$('create-submit').disabled=false;}
};

function openDelete(item){pendingDelete=item;error('delete-error','');$('delete-name').value='';const workspace=item.kind==='workspace';$('delete-title').textContent=workspace?'Delete this workspace?':'Remove this material?';$('delete-copy').textContent=workspace?`This permanently deletes “${item.name}” and everything saved inside it.`:`This permanently removes “${item.name}” and its extracted page data.`;$('delete-name-field').hidden=!workspace;$('confirm-delete').textContent=workspace?'Delete workspace':'Remove material';updateDeleteButton();$('delete-dialog').showModal();if(workspace)$('delete-name').focus();}
function updateDeleteButton(){$('confirm-delete').disabled=!pendingDelete||(pendingDelete.kind==='workspace'&&$('delete-name').value!==pendingDelete.name);}
async function confirmDelete(){if(!pendingDelete)return;const item=pendingDelete;$('confirm-delete').disabled=true;error('delete-error','');try{if(item.kind==='workspace'){await api(`/workspaces/${item.id}`,{method:'DELETE'});$('delete-dialog').close();pendingDelete=null;await loadWorkspaces();toast('Workspace deleted.');}else{await api(`/documents/${item.id}`,{method:'DELETE'});$('delete-dialog').close();pendingDelete=null;await loadDocuments(activeWorkspace);toast('Material removed.');}}catch(e){error('delete-error',e.message);updateDeleteButton();}}
window.addEventListener('ark:enter-workbench',async event=>{const session=event.detail?.session;if(session)await showWorkspace(session);else{history.replaceState({},'',`/login/${portal}`);showAuth();}});
(async()=>{setPortal(portal,false);let session=null;try{session=await api('/auth/me');}catch{/* Secure access remains available when there is no session. */}if(location.pathname.startsWith('/login/')){if(session)await showWorkspace(session);else showAuth();return;}if(window.ARKLanding){$('auth-view').hidden=true;$('workspace-view').hidden=true;await window.ARKLanding.show(session);}else if(session)await showWorkspace(session);else showAuth();})();

function formatSize(bytes){return bytes < 1024*1024 ? `${Math.ceil(bytes/1024)} KB` : `${(bytes/1024/1024).toFixed(1)} MB`;}
let materialFilter='all';
function applyMaterialFilters(){const query=$('material-search').value.trim().toLowerCase();let visible=0;document.querySelectorAll('#document-list .document-row,#reference-list .document-row').forEach(row=>{const matchName=!query||row.dataset.name.includes(query);const matchState=materialFilter==='all'||row.dataset.readiness===materialFilter;row.hidden=!(matchName&&matchState);if(!row.hidden)visible++;});$('material-no-match').hidden=visible>0||!document.querySelector('#document-list .document-row');}
$('material-search').addEventListener('input',applyMaterialFilters);
document.querySelectorAll('[data-material-filter]').forEach(button=>button.addEventListener('click',()=>{materialFilter=button.dataset.materialFilter;document.querySelectorAll('[data-material-filter]').forEach(item=>item.classList.toggle('active',item===button));applyMaterialFilters();}));
function renderDocumentRows(list, docs, kind, workspaceId){
  list.replaceChildren();
  if(!docs.length){const empty=document.createElement('div');empty.className='compact-empty';empty.innerHTML=kind==='report'?'<span>▤</span><h3>No incident reports yet</h3><p>Drop an incident report above to create a case record.</p>':'<span>▥</span><h3>No reference materials yet</h3><p>An Administrator can add approved SOPs, manuals and maintenance history.</p>';list.append(empty);return;}
  for(const doc of docs){
    const row=document.createElement('div');row.className=`document-row ${kind==='report'?'report-row':'reference-row'}`;row.dataset.name=doc.filename.toLowerCase();row.dataset.readiness=doc.extracted?'ready':'unread';
    const info=document.createElement('div');info.className='document-info';const type=document.createElement('span');type.className='file-type';type.textContent=(doc.filename.split('.').pop()||'FILE').toUpperCase();const infoText=document.createElement('div');const name=document.createElement('strong');name.textContent=doc.filename;
    const meta=document.createElement('p');meta.textContent=kind==='report'?`${doc.report_id} · ${doc.status} · ${formatSize(doc.size)}`:`${formatSize(doc.size)} · ${doc.extracted?'Ready for source questions':'Unread'}`;infoText.append(name,meta);
    if(kind==='report'){const progress=document.createElement('div');progress.className='report-progress';const fill=document.createElement('span');fill.style.width=`${doc.progress}%`;progress.append(fill);infoText.append(progress);}
    info.append(type,infoText);const link=document.createElement('a');link.className='secondary';link.href=`/api/documents/${doc.id}/download`;link.textContent='Download';link.setAttribute('download',doc.filename);const actions=document.createElement('div');actions.className='file-actions';actions.append(link);const fileExt=(doc.filename.split('.').pop()||'').toLowerCase();const docActions=activeReadOnly?[[doc.extracted?'View sources':'Not yet read',()=>showSource(doc.id)]]:[[doc.extracted?'Read again':'Read locally',()=>readMaterial(doc.id,workspaceId)],['View sources',()=>showSource(doc.id)]];
    if(kind==='report'&&!activeReadOnly&&['pdf','png','jpg','jpeg'].includes(fileExt))docActions.push(['Describe image',()=>describeImage(doc.id,workspaceId)]);if(kind==='report'&&!activeReadOnly)docActions.push(['Create review pack',()=>startReview(doc.id,workspaceId)]);
    for(const [label,action] of docActions){const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=label;button.onclick=action;if(activeReadOnly&&!doc.extracted)button.disabled=true;actions.append(button);}if(!activeReadOnly&&(kind==='report'||user.role==='administrator')){const remove=document.createElement('button');remove.type='button';remove.className='danger-button';remove.textContent='Remove';remove.onclick=()=>openDelete({kind:'document',id:doc.id,name:doc.filename});actions.append(remove);}row.append(info,actions);list.append(row);
  }
}
async function loadDocuments(id){
  const [reports, references]=await Promise.all([api(`/workspaces/${id}/documents?kind=report`),api(`/workspaces/${id}/documents?kind=reference`)]);if(activeWorkspace!==id)return;
  const all=[...reports.documents,...references.documents],read=all.filter(doc=>doc.extracted).length;renderDocumentRows($('document-list'),reports.documents,'report',id);renderDocumentRows($('reference-list'),references.documents,'reference',id);$('metric-documents').textContent=all.length;$('metric-read').textContent=`${read} ready for questions`;$('material-summary').textContent=`${reports.documents.length} ${reports.documents.length===1?'report':'reports'} · ${reports.documents.filter(doc=>doc.extracted).length} read`;$('reference-summary').textContent=`${references.documents.length} ${references.documents.length===1?'file':'files'}`;$('use-documents').disabled=activeReadOnly||read===0;if(read===0||activeReadOnly)$('use-documents').checked=false;$('source-readiness').textContent=activeReadOnly?'Supervisor review mode is read-only':read?`${read} read ${read===1?'material':'materials'} available for grounding`:'Read material to enable source-grounded answers';applyMaterialFilters();
}
$('material-files').addEventListener('change',async event=>{
  if(uploading)return;
  const files=Array.from(event.target.files);const id=activeWorkspace;if(!id||!files.length)return;
  uploading=true;event.target.disabled=true;error('upload-error','');let succeeded=0;const failures=[];
  try{
    for(let i=0;i<files.length;i++){
      const file=files[i];$('upload-status').textContent=`Uploading ${i+1} of ${files.length}: ${file.name}`;
      try{
        if(file.size>20*1024*1024)throw new Error('File exceeds 20 MB.');
        await api(`/workspaces/${id}/documents?filename=${encodeURIComponent(file.name)}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});succeeded++;
      }catch(e){failures.push(`${file.name}: ${e.message}`);}
    }
    $('upload-status').textContent=`${succeeded} of ${files.length} files uploaded.`;
    if(failures.length)error('upload-error',failures.join(' '));
    if(activeWorkspace===id)await loadDocuments(id);
  }catch(e){error('upload-error',e.message);}finally{uploading=false;event.target.disabled=false;event.target.value='';}
});

$('reference-files').addEventListener('change',async event=>{
  if(uploading||user.role!=='administrator')return;const files=Array.from(event.target.files);const id=activeWorkspace;if(!id||!files.length)return;uploading=true;event.target.disabled=true;error('reference-upload-error','');let succeeded=0;const failures=[];
  try{for(let i=0;i<files.length;i++){const file=files[i];$('reference-upload-status').textContent=`Uploading ${i+1} of ${files.length}: ${file.name}`;try{if(file.size>20*1024*1024)throw new Error('File exceeds 20 MB.');await api(`/workspaces/${id}/documents?filename=${encodeURIComponent(file.name)}&kind=reference`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});succeeded++;}catch(e){failures.push(`${file.name}: ${e.message}`);}}$('reference-upload-status').textContent=`${succeeded} of ${files.length} reference files uploaded.`;if(failures.length)error('reference-upload-error',failures.join(' '));if(activeWorkspace===id)await loadDocuments(id);}catch(e){error('reference-upload-error',e.message);}finally{uploading=false;event.target.disabled=false;event.target.value='';}
});

let generating=false;
async function loadModels(){
  try{const result=await api('/models');const ready=result.models.filter(m=>m.status==='installed'||m.status==='running').length;$('models-status').textContent=`${ready} LOCAL MODELS AVAILABLE`;$('models-top-status').textContent=`${ready} models ready`;$('metric-models').textContent=ready;}
  catch{$('models-status').textContent='MODELS UNAVAILABLE';$('models-top-status').textContent='Models unavailable';$('metric-models').textContent='0';}
}
let answerFilter='all';
function inlineRichText(text){const fragment=document.createDocumentFragment();const pattern=/(\*\*[^*]+\*\*|`[^`]+`|\[S\d+\])/g;let last=0;for(const match of text.matchAll(pattern)){if(match.index>last)fragment.append(document.createTextNode(text.slice(last,match.index)));const token=match[0];if(token.startsWith('**')){const strong=document.createElement('strong');strong.textContent=token.slice(2,-2);fragment.append(strong);}else if(token.startsWith('`')){const code=document.createElement('code');code.textContent=token.slice(1,-1);fragment.append(code);}else{const citation=document.createElement('span');citation.className='citation-badge';citation.textContent=token;fragment.append(citation);}last=match.index+token.length;}if(last<text.length)fragment.append(document.createTextNode(text.slice(last)));return fragment;}
function renderRichAnswer(markdown){
  const root=document.createElement('div');root.className='rich-answer';const lines=String(markdown||'').replace(/\r/g,'').split('\n');
  for(let i=0;i<lines.length;){const line=lines[i];if(!line.trim()){i++;continue;}
    if(/^\s*\|/.test(line)&&i+1<lines.length&&/^\s*\|?\s*:?-{2,}/.test(lines[i+1])){const table=document.createElement('table');table.className='answer-table';const head=document.createElement('thead');const body=document.createElement('tbody');const cells=value=>value.trim().replace(/^\|/,'').replace(/\|$/,'').split('|').map(cell=>cell.trim());const tr=document.createElement('tr');for(const cell of cells(line)){const th=document.createElement('th');th.append(inlineRichText(cell));tr.append(th);}head.append(tr);i+=2;while(i<lines.length&&/^\s*\|/.test(lines[i])){const row=document.createElement('tr');for(const cell of cells(lines[i])){const td=document.createElement('td');td.append(inlineRichText(cell));row.append(td);}body.append(row);i++;}table.append(head,body);root.append(table);continue;}
    const heading=line.match(/^\s*#{1,6}\s+(.+)/);if(heading){const h=document.createElement(heading[0].trim().startsWith('# ')||heading[0].trim().startsWith('## ')?'h3':'h4');h.append(inlineRichText(heading[1]));root.append(h);i++;continue;}
    const list=line.match(/^\s*[-*]\s+(.+)/);if(list){const ul=document.createElement('ul');while(i<lines.length){const item=lines[i].match(/^\s*[-*]\s+(.+)/);if(!item)break;const li=document.createElement('li');li.append(inlineRichText(item[1]));ul.append(li);i++;}root.append(ul);continue;}
    const ordered=line.match(/^\s*\d+[.)]\s+(.+)/);if(ordered){const ol=document.createElement('ol');while(i<lines.length){const item=lines[i].match(/^\s*\d+[.)]\s+(.+)/);if(!item)break;const li=document.createElement('li');li.append(inlineRichText(item[1]));ol.append(li);i++;}root.append(ol);continue;}
    const paragraph=document.createElement('p');paragraph.append(inlineRichText(line));root.append(paragraph);i++;
  }return root;
}
function applyAnswerFilter(){let visible=0;document.querySelectorAll('#generation-list .answer-card').forEach(card=>{card.hidden=answerFilter!=='all'&&card.dataset.answerType!==answerFilter;if(!card.hidden)visible++;});$('answer-no-match').hidden=visible>0||!document.querySelector('#generation-list .answer-card');}
document.querySelectorAll('[data-answer-filter]').forEach(button=>button.addEventListener('click',()=>{answerFilter=button.dataset.answerFilter;document.querySelectorAll('[data-answer-filter]').forEach(item=>item.classList.toggle('active',item===button));applyAnswerFilter();}));
async function loadGenerations(id){
  const data=await api(`/workspaces/${id}/generations`);if(activeWorkspace!==id)return;
  const list=$('generation-list');list.replaceChildren();$('metric-answers').textContent=data.generations.length;$('answer-count').textContent=data.generations.length;$('answer-empty').hidden=data.generations.length>0;
  for(const item of data.generations){
    const card=document.createElement('article');card.className='answer-card';card.dataset.answerType=(item.sources||[]).length?'sources':'general';
    const title=document.createElement('h3');title.textContent=item.prompt;
    const kind=document.createElement('span');kind.className='answer-kind';kind.textContent=card.dataset.answerType==='sources'?'Source-grounded':'General';
    const meta=document.createElement('p');meta.className='answer-meta';meta.textContent=`${item.model_name} · ${(item.duration_ms/1000).toFixed(1)} seconds · ${item.capability}`;
    const reason=document.createElement('p');reason.className='field-help';reason.textContent=`Auto-selection: ${item.routing_reason}`;
    const answer=renderRichAnswer(item.answer);
    const cardActions=document.createElement('div');cardActions.className='answer-actions';const copy=document.createElement('button');copy.className='text-button';copy.textContent='Copy answer';copy.onclick=async()=>{await navigator.clipboard.writeText(item.answer);toast('Answer copied.');};cardActions.append(copy);card.append(kind,title,meta,reason,answer,cardActions);
    if(item.review_note){const note=document.createElement('p');note.className='field-help';note.textContent=item.review_note;card.append(note);}
    if(item.citation_format_valid===false){const warn=document.createElement('p');warn.className='error';warn.textContent='The answer did not use valid source references. Check the excerpts before relying on it.';card.append(warn);}
    for(const source of item.sources||[]){const link=document.createElement('button');link.className='source-link';link.textContent=`[${source.ref}] ${source.filename} · page ${source.page}`;link.onclick=()=>showSource(source.document_id,source.page);card.append(link);}
    if(item.finish_reason==='length'){const warning=document.createElement('p');warning.className='field-help';warning.textContent='The answer reached the prototype response limit. Request a shorter answer if needed.';card.append(warning);}
    list.append(card);
  }
  applyAnswerFilter();
}
$('prompt-form').addEventListener('submit',async event=>{
  event.preventDefault();if(generating||!activeWorkspace)return;
  const id=activeWorkspace;const prompt=$('task-prompt').value.trim();if(!prompt)return;
  generating=true;$('generate-button').disabled=true;error('generation-error','');
  const started=Date.now();$('generation-status').textContent='Starting the selected local model…';
  const timer=setInterval(()=>{if(activeWorkspace===id)$('generation-status').textContent=`Working locally… ${Math.floor((Date.now()-started)/1000)}s. First use includes model loading.`;},1000);
  try{
    const payload={prompt};if($('use-documents').checked&&assistantDocumentIds.length)payload.document_id=assistantDocumentIds[0];const result=await api(`/workspaces/${id}/${$('use-documents').checked?'questions':'generations'}`,{method:'POST',body:JSON.stringify(payload)});
    if(activeWorkspace===id){$('generation-status').textContent=result.review_request_id?'Analysis complete. Sent to the Supervisor review queue.':'Answer saved in this workspace.';await loadGenerations(id);await loadModels();await loadReviewQueue();}
  }catch(e){if(activeWorkspace===id){error('generation-error',e.message);$('generation-status').textContent='Request did not complete.';}}
  finally{clearInterval(timer);generating=false;$('generate-button').disabled=false;}
});

$('use-documents').onchange=()=>{$('task-prompt').maxLength=$('use-documents').checked?800:2000;};
$('task-prompt').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('prompt-form').requestSubmit();}});
async function uploadAssistantFiles(files){
  if(uploading||activeReadOnly||!activeWorkspace)return;
  uploading=true;$('assistant-files').disabled=true;error('assistant-upload-error','');let done=0;const failures=[];
  try{for(const file of files){try{if(file.size>20*1024*1024)throw new Error('File exceeds 20 MB.');const item=await api(`/workspaces/${activeWorkspace}/documents?filename=${encodeURIComponent(file.name)}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});await api(`/documents/${item.id}/extract`,{method:'POST'});if(/\.(png|jpe?g)$/i.test(file.name)){try{await api(`/documents/${item.id}/vision`,{method:'POST'});}catch(e){/* OCR remains available when the local vision model is unavailable. */}}assistantDocumentIds.push(item.id);const chip=document.createElement('span');chip.className='assistant-file-chip';chip.textContent=`${file.name} · ready`;$('assistant-file-list').append(chip);done++;}catch(e){failures.push(`${file.name}: ${e.message}`);}$('assistant-upload-status').textContent=`${done} of ${files.length} incident files ready for analysis.`;}if(done){$('use-documents').checked=true;$('use-documents').disabled=false;$('source-readiness').textContent=`${done} incident file${done===1?'':'s'} ready for grounded analysis`;$('assistant-review-pack').disabled=false;}if(failures.length)error('assistant-upload-error',failures.join(' '));await loadDocuments(activeWorkspace);await loadGenerations(activeWorkspace);}finally{uploading=false;$('assistant-files').disabled=activeReadOnly;$('assistant-files').value='';}
}
$('assistant-files').addEventListener('change',event=>uploadAssistantFiles(Array.from(event.target.files)));
const assistantDrop=$('assistant-drop-zone');['dragenter','dragover'].forEach(type=>assistantDrop.addEventListener(type,event=>{event.preventDefault();assistantDrop.classList.add('dragging');}));['dragleave','drop'].forEach(type=>assistantDrop.addEventListener(type,event=>{event.preventDefault();assistantDrop.classList.remove('dragging');}));assistantDrop.addEventListener('drop',event=>{if(event.dataTransfer.files.length)uploadAssistantFiles(Array.from(event.dataTransfer.files));});
$('close-source').onclick=()=>$('source-dialog').close();
async function readMaterial(documentId,workspace){
  error('upload-error','');$('upload-status').textContent='Reading locally. Scanned pages use OCR…';
  try{await api(`/documents/${documentId}/extract`,{method:'POST'});if(activeWorkspace===workspace){$('upload-status').textContent='Text extracted. Check the source before using its contents.';await loadDocuments(workspace);await showSource(documentId);}}
  catch(e){error('upload-error',e.message);$('upload-status').textContent='Document reading did not complete.';}
}
async function showSource(documentId,pageNumber){
  try{const data=await api(`/documents/${documentId}/pages`);const area=$('source-pages');area.replaceChildren();
    if(!data.pages.length){const p=document.createElement('p');p.textContent='Read this material first to extract its text.';area.append(p);}
    for(const page of data.pages){const section=document.createElement('section');section.id=`source-page-${page.page}`;const title=document.createElement('h3');title.textContent=`Page ${page.page} · ${page.method}`;section.append(title);
      for(const message of page.warnings){const p=document.createElement('p');p.className='field-help';p.textContent=message;section.append(p);}
      if(page.method!=='text'){const image=document.createElement('img');image.src=`/api/documents/${documentId}/pages/${page.page}/image`;image.alt=`Original page ${page.page}`;image.loading='lazy';section.append(image);}
      const text=document.createElement('pre');text.className='answer-text';text.textContent=page.text||'No readable text was extracted.';section.append(text);area.append(section);}
    if(!$('source-dialog').open)$('source-dialog').showModal();if(pageNumber)$(`source-page-${pageNumber}`)?.scrollIntoView();
  }catch(e){toast(e.message);}
}
async function describeImage(documentId,workspace){$('upload-status').textContent='Reading the image with the local vision model…';error('upload-error','');try{await api(`/documents/${documentId}/vision`,{method:'POST'});if(activeWorkspace===workspace){$('upload-status').textContent='Visual description saved in Assistant.';await loadGenerations(workspace);showTab('assistant');toast('Visual description is ready.');}}catch(e){error('upload-error',e.message);$('upload-status').textContent='Vision request did not complete.';}}
async function startReview(documentId,workspace,stayOnAssistant=false){try{await api(`/workspaces/${workspace}/runs`,{method:'POST',body:JSON.stringify({document_id:documentId})});if(stayOnAssistant){showTab('assistant');toast('Incident review started. Deliverables will appear here when ready.');}else{showTab('workflows');toast('Review workflow started.');}await loadRuns(workspace);}catch(e){error(stayOnAssistant?'generation-error':'upload-error',e.message);}}
$('assistant-review-pack').onclick=()=>{if(assistantDocumentIds[0])startReview(assistantDocumentIds[0],activeWorkspace,true);};
$('run-code').onclick=async()=>{if(!activeWorkspace)return;error('run-error','');$('run-code').disabled=true;try{await api(`/workspaces/${activeWorkspace}/code-runs`,{method:'POST',body:JSON.stringify({utility:$('code-utility').value})});toast('Verification workflow started.');await loadRuns(activeWorkspace);}catch(e){error('run-error',e.message);}finally{$('run-code').disabled=false;}};
let runFilter='all';
function applyRunFilter(){let visible=0;document.querySelectorAll('#run-list .answer-card').forEach(card=>{card.hidden=runFilter!=='all'&&card.dataset.runStatus!==runFilter;if(!card.hidden)visible++;});$('run-no-match').hidden=visible>0||!document.querySelector('#run-list .answer-card');}
document.querySelectorAll('[data-run-filter]').forEach(button=>button.addEventListener('click',()=>{runFilter=button.dataset.runFilter;document.querySelectorAll('[data-run-filter]').forEach(item=>item.classList.toggle('active',item===button));applyRunFilter();}));
function renderAssistantDeliverables(runs){const completed=runs.find(run=>run.status==='complete'&&(run.result.artifacts||[]).length);const section=$('assistant-deliverables');const list=$('assistant-artifact-list');list.replaceChildren();if(!completed){section.hidden=true;return;}section.hidden=false;const label=document.createElement('strong');label.textContent=`${completed.kind==='coding'?'Verified utility':'Inspection review pack'} · ${new Date(completed.created_at*1000).toLocaleString()}`;list.append(label);for(const artifact of completed.result.artifacts){const link=document.createElement('a');link.className='secondary artifact-link';link.href=`/api/artifacts/${artifact.id}/download`;link.textContent=artifact.filename;list.append(link);}}
async function loadRuns(id){
 try{const data=await api(`/workspaces/${id}/runs`);if(activeWorkspace!==id)return;const list=$('run-list');list.replaceChildren();const complete=data.runs.filter(run=>run.status==='complete').length;$('metric-runs').textContent=data.runs.length;$('metric-complete').textContent=`${complete} completed`;$('run-count').textContent=data.runs.length;$('run-empty').hidden=data.runs.length>0;
 const activity=$('overview-activity');activity.replaceChildren();for(const run of data.runs.slice(0,4)){const row=document.createElement('div');row.className='activity-item';const icon=document.createElement('span');icon.textContent=run.status==='complete'?'✓':'↻';const details=document.createElement('div');const name=document.createElement('strong');name.textContent=run.kind==='coding'?'Verified utility':'Inspection review pack';const meta=document.createElement('small');meta.textContent=`${run.status==='complete'?'Completed':run.status} · ${new Date(run.created_at*1000).toLocaleString()}`;details.append(name,meta);row.append(icon,details);activity.append(row);}if(!data.runs.length){const p=document.createElement('p');p.className='empty-copy';p.textContent='No activity yet. Add your first material to begin.';activity.append(p);}
 for(const run of data.runs){const card=document.createElement('article');card.className='answer-card workflow-card';card.dataset.runStatus=run.status;const header=document.createElement('div');header.className='workflow-card-header';const heading=document.createElement('div');const title=document.createElement('h3');title.textContent=run.kind==='coding'?'Code verification':'Inspection review pack';const created=document.createElement('small');created.textContent=new Date(run.created_at*1000).toLocaleString();heading.append(title,created);const badge=document.createElement('span');badge.className=`run-status ${run.status}`;badge.textContent=run.status;header.append(heading,badge);const progress=document.createElement('div');progress.className='run-progress';const fill=document.createElement('span');fill.style.width=run.status==='complete'?'100%':run.status==='failed'?'100%':`${Math.min(90,Math.max(12,(run.events||[]).length*18))}%`;progress.append(fill);card.append(header,progress);
 const events=document.createElement('ol');events.className='run-events';for(const event of run.events){const li=document.createElement('li');li.textContent=event.message;events.append(li);}card.append(events);
 if(run.result.error){const error=document.createElement('p');error.className='error';error.textContent=run.result.error;card.append(error);}
 if(run.result.draft){card.append(renderRichAnswer(run.result.draft));}else if(run.result.code){const text=document.createElement('pre');text.className='answer-text';text.textContent=run.result.code;card.append(text);}
 for(const check of run.result.checks||[]){const p=document.createElement('p');p.className='field-help';p.textContent=`${check.passed?'PASS':'FAIL'} · Input ${JSON.stringify(check.input)} → ${JSON.stringify(check.actual)} (expected ${check.expected})`;card.append(p);}
 if((run.result.artifacts||[]).length){const downloads=document.createElement('div');downloads.className='artifact-group';const label=document.createElement('strong');label.textContent='Deliverables';downloads.append(label);for(const artifact of run.result.artifacts){const link=document.createElement('a');link.className='secondary artifact-link';link.href=`/api/artifacts/${artifact.id}/download`;link.textContent=artifact.filename;downloads.append(link);}card.append(downloads);}list.append(card);}
 renderAssistantDeliverables(data.runs);applyRunFilter();
 }catch(e){error('run-error',e.message);}
}
setInterval(()=>{if(activeWorkspace&&!document.hidden){loadRuns(activeWorkspace);loadReviewQueue();}},2500);

document.querySelectorAll('.suggestion').forEach(button=>button.onclick=()=>{$('task-prompt').value=button.textContent;$('task-prompt').focus();});
const dropZone=$('drop-zone');
['dragenter','dragover'].forEach(type=>dropZone.addEventListener(type,event=>{event.preventDefault();dropZone.classList.add('dragging');}));
['dragleave','drop'].forEach(type=>dropZone.addEventListener(type,event=>{event.preventDefault();dropZone.classList.remove('dragging');}));
dropZone.addEventListener('drop',event=>{if(event.dataTransfer.files.length){const transfer=new DataTransfer();Array.from(event.dataTransfer.files).forEach(file=>transfer.items.add(file));$('material-files').files=transfer.files;$('material-files').dispatchEvent(new Event('change'));}});
const referenceDropZone=$('reference-drop-zone');
['dragenter','dragover'].forEach(type=>referenceDropZone.addEventListener(type,event=>{event.preventDefault();referenceDropZone.classList.add('dragging');}));
['dragleave','drop'].forEach(type=>referenceDropZone.addEventListener(type,event=>{event.preventDefault();referenceDropZone.classList.remove('dragging');}));
referenceDropZone.addEventListener('drop',event=>{if(event.dataTransfer.files.length&&user.role==='administrator'){const transfer=new DataTransfer();Array.from(event.dataTransfer.files).forEach(file=>transfer.items.add(file));$('reference-files').files=transfer.files;$('reference-files').dispatchEvent(new Event('change'));}});

async function loadNetwork(){if(!user)return;try{const data=await api('/system/network');const external=data.external_connections.length;$('network-summary').textContent=`${data.samples} samples · ${external} external connections observed · ${(data.blocked_python_attempts||[]).length} blocked Python attempts`;$('network-detail').textContent=`Python outbound guard enabled. Observation errors: ${data.observation_errors}. Packet capture: ${data.packet_capture.replaceAll('_',' ')}.`;$('network-badge').classList.toggle('attention',external>0);$('network-badge').lastChild.textContent=external?' Review required':' No external connections observed';}catch{$('network-summary').textContent='Connection observations unavailable.';$('network-badge').lastChild.textContent=' Monitor unavailable';}}
setInterval(()=>{if(user&&!document.hidden)loadNetwork();},3000);

$('read-all').onclick=async()=>{const id=activeWorkspace;if(!id)return;$('read-all').disabled=true;error('upload-error','');let count=0;try{const data=await api(`/workspaces/${id}/documents`);for(const doc of data.documents){if(doc.extracted)continue;$('upload-status').textContent=`Reading ${doc.filename}…`;await api(`/documents/${doc.id}/extract`,{method:'POST'});count++;}if(activeWorkspace===id){$('upload-status').textContent=`Read ${count} new materials. Source-grounded questions can now use this collection.`;await loadDocuments(id);}}catch(e){error('upload-error',e.message);}finally{$('read-all').disabled=false;}};
