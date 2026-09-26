/* Same-origin case interface. Source text is always rendered as text, never HTML. */
(() => {
  let loading = false;
  const el = (tag, text, cls) => {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const stageNames={awaiting_confirmation:'Needs engineer confirmation',awaiting_verification:'Calculation ready for checks',pending_approval:'Awaiting separate reviewer',approved:'Approved for export',rejected:'Returned for revision',verification_failed:'Verification failed'};
  async function loadCases(){
    if(!activeWorkspace||!user||loading)return;
    loading=true;const workspace=activeWorkspace;
    try{const data=await api(`/workspaces/${workspace}/investigations`);if(activeWorkspace!==workspace)return;
      const list=$('case-list');list.replaceChildren();
      $('case-create').disabled=activeReadOnly;
      if(!data.cases.length)list.append(el('p','No cases yet. Start with the conflicting-reading demo or your extracted materials.','case-empty'));
      data.cases.forEach(item=>list.append(renderCase(item)));
    }catch(e){error('case-error',e.message);}finally{loading=false;}
  }
  function renderCase(c){
    const card=el('article',undefined,'investigation-card');
    const head=el('div',undefined,'case-heading');head.append(el('h3',`${c.tag} · Thickness investigation`),el('span',stageNames[c.status]||c.status,'case-stage'));card.append(head);
    card.append(el('p',c.synthetic?'SYNTHETIC DEMO DATA · Not a real MRPL inspection':'WORKSPACE EVIDENCE · Engineer must confirm applicability','case-label'));
    const stages=['Retrieve evidence','Confirm inputs','Calculate','Verify','Human approval'];
    const position={awaiting_confirmation:1,awaiting_verification:3,pending_approval:4,approved:5,rejected:4,verification_failed:3}[c.status];
    const timeline=el('div',undefined,'case-timeline');stages.forEach((s,i)=>timeline.append(el('span',`${i+1}. ${s}`,i<position?'done':i===position?'current':'')));card.append(timeline);
    const sources=el('div',undefined,'case-sources');const checked=[];
    for(const s of c.sources){const details=el('details',undefined,`case-source ${s.status}`);const summary=el('summary',`${s.status==='included'?'Retained':'Excluded'} · ${s.filename} · p.${s.page} · Rev ${s.revision}`);details.append(summary,el('p',s.reason),el('pre',s.text));
      if(s.status==='included'){const label=el('label',undefined,'case-check');const box=el('input');box.type='checkbox';box.disabled=c.status!=='awaiting_confirmation'||activeReadOnly;box.checked=(c.inputs?.source_ids||[]).includes(s.id);label.append(box,el('span','Use this page as confirmed evidence'));details.append(label);checked.push({id:s.id,box});}
      sources.append(details);
    }card.append(sources);
    if(!c.sources.some(s=>s.status==='included'))card.append(el('p','No usable source pages. Add correctly tagged, revision-labelled evidence and start a new case.','case-label'));
    const inputs=el('div',undefined,'case-inputs');const fields={};
    for(const [key,label] of [['previous_mm','Previous thickness (mm)'],['current_mm','Current thickness (mm)'],['interval_years','Elapsed time (years)']]){const wrap=el('label',label);const input=el('input');input.type='number';input.step='any';input.min='0.000001';input.placeholder='Confirm from sources';input.value=c.inputs?.[key]??'';input.disabled=c.status!=='awaiting_confirmation'||activeReadOnly;fields[key]=input;wrap.append(input);inputs.append(wrap);}card.append(inputs);
    if(c.inputs)card.append(el('p',`Engineer confirmation: ${c.inputs.confirmation_note}`));
    if(c.result){const result=el('div',undefined,'case-result');result.append(el('strong',`${c.result.rate_mm_per_year.toFixed(4)} mm/year`),el('p',c.result.formula),el('p',`Arithmetic cross-check: ${c.result.verification}`),el('p',c.result.limitation));card.append(result);}
    const note=el('textarea',undefined,'case-note');note.placeholder=c.status==='pending_approval'?'Reviewer: explain your decision after checking the evidence and calculation.':'Explain the source revisions, selected readings and resolution of any conflict.';note.maxLength=1200;note.setAttribute('aria-label','Confirmation or review note');card.append(note);
    const actions=el('div',undefined,'case-actions');
    function button(text,handler,disabled=false){const b=el('button',text,'secondary');b.type='button';b.disabled=disabled;b.onclick=handler;actions.append(b);return b;}
    async function act(action,extra={}){actions.querySelectorAll('button').forEach(b=>b.disabled=true);error('case-error','');try{await api(`/investigations/${c.id}/actions`,{method:'POST',body:JSON.stringify({action,version:c.version,note:note.value,...extra})});await loadCases();}catch(e){error('case-error',e.message);actions.querySelectorAll('button').forEach(b=>b.disabled=false);}}
    if(c.status==='awaiting_confirmation'&&!activeReadOnly)button('Confirm evidence & calculate',()=>act('confirm',{previous_mm:Number(fields.previous_mm.value),current_mm:Number(fields.current_mm.value),interval_years:Number(fields.interval_years.value),source_ids:checked.filter(x=>x.box.checked).map(x=>x.id)}));
    if(c.status==='awaiting_verification'&&!activeReadOnly)button('Run arithmetic cross-check',()=>act('verify'));
    if(c.status==='pending_approval'&&['supervisor','administrator'].includes(user.role)&&user.id!==c.created_by&&user.id!==c.inputs?.confirmed_by){button('Approve exact version',()=>act('approve'));button('Return for revision',()=>act('reject'));}
    else if(c.status==='pending_approval')card.append(el('p','A different Supervisor or Administrator must review and approve this case.','case-label'));
    if(c.status!=='awaiting_confirmation'&&!activeReadOnly)button('Reopen & revoke approval',()=>{if(window.confirm('Reopen this case? Confirmed inputs, checks and any approval will be cleared.'))act('revise');});
    button(c.status==='approved'?'Export approved case':'Export locked until approval',async()=>{try{const response=await fetch(`/api/investigations/${c.id}/export`,{credentials:'same-origin',headers:{'X-Workbench-Request':'1'}});if(!response.ok){const data=await response.json();throw new Error(data.detail);}const url=URL.createObjectURL(await response.blob());const a=el('a');a.href=url;a.download=`ARK-${c.tag}-approved.html`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){error('case-error',e.message);}},c.status!=='approved');card.append(actions);
    if(c.approval)card.append(el('p',`Approved by ${c.approval.reviewer} · SHA-256 ${c.approval.digest.slice(0,16)}… · ${c.approval.note}`));
    const log=el('details',undefined,'case-log');log.append(el('summary',`Audit trail · version ${c.version} · ${c.events.length} events`));const ol=el('ol');for(const e of c.events)ol.append(el('li',`${new Date(e.at*1000).toLocaleTimeString()} · ${e.actor}: ${e.message}`));log.append(ol);card.append(log);return card;
  }
  $('case-refresh').onclick=loadCases;
  $('case-create').onclick=async()=>{if(!activeWorkspace)return;error('case-error','');$('case-create').disabled=true;try{await api(`/workspaces/${activeWorkspace}/investigations`,{method:'POST',body:JSON.stringify({tag:$('case-tag').value.trim(),scenario:$('case-scenario').value})});await loadCases();}catch(e){error('case-error',e.message);}finally{$('case-create').disabled=activeReadOnly;}};
  // Observe workspace changes, without interrupting in-progress confirmation forms.
  let workspace=null;
  setInterval(()=>{if(activeWorkspace!==workspace){workspace=activeWorkspace;$('case-list').replaceChildren();if(workspace)loadCases();}},600);
})();
