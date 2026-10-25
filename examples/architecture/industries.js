(() => {
  'use strict';
  const scene = document.body.dataset.industry;
  const openers = new WeakMap();
  document.querySelectorAll('[data-open]').forEach(button => button.addEventListener('click', () => {
    const dialog = document.getElementById(button.dataset.open); openers.set(dialog, button); dialog.showModal();
  }));
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelector('.close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => openers.get(dialog)?.focus());
  });
  if (scene === 'hotel') {
    const form = document.querySelector('#stay-form'), status = document.querySelector('#stay-status');
    const arrival = form.elements.arrival, departure = form.elements.departure;
    function validate() { departure.setCustomValidity(departure.value && arrival.value && departure.value <= arrival.value ? '离店日期须晚于入住日期' : ''); }
    arrival.addEventListener('input', validate); departure.addEventListener('input', validate);
    try { const saved = JSON.parse(localStorage.getItem('tideline:plan') || 'null'); if (saved && /^\d{4}-\d{2}-\d{2}$/.test(saved.arrival) && /^\d{4}-\d{2}-\d{2}$/.test(saved.departure) && saved.departure > saved.arrival && ['1 人','2 人','3 人','4 人'].includes(saved.guests)) { arrival.value=saved.arrival; departure.value=saved.departure; form.elements.guests.value=saved.guests; status.textContent=`已保存 ${saved.arrival} 至 ${saved.departure}`; } } catch { /* Leave the form usable when no readable plan exists. */ }
    form.addEventListener('submit', event => { event.preventDefault(); validate(); if (!form.reportValidity()) return; const plan = Object.fromEntries(new FormData(form)); try {localStorage.setItem('tideline:plan', JSON.stringify(plan)); status.textContent=`已保存 ${plan.arrival} 至 ${plan.departure}`;} catch {status.textContent='保存失败 请保留当前选择';} });
  }
  if (scene === 'architecture') {
    const form=document.querySelector('#project-form'), status=document.querySelector('#project-status');
    try {const saved=JSON.parse(localStorage.getItem('jianxu:intent')||'null');if(saved&&['住宅','商业空间','公共空间'].includes(saved.type)&&typeof saved.idea==='string'){form.elements.type.value=saved.type;form.elements.idea.value=saved.idea;}}catch{ /* A new local draft remains available. */ }
    form.addEventListener('submit',event=>{event.preventDefault();if(!form.elements.idea.value.trim()){form.elements.idea.setCustomValidity('请填写项目想法');form.reportValidity();return;}try{localStorage.setItem('jianxu:intent',JSON.stringify(Object.fromEntries(new FormData(form))));status.textContent='已在本机保存';}catch{status.textContent='保存失败 请保留当前内容';}});
    form.elements.idea.addEventListener('input',()=>form.elements.idea.setCustomValidity(''));
  }
  if (scene === 'coffee') {
    const form=document.querySelector('#coffee-form'), list=document.querySelector('#coffee-list'), status=document.querySelector('#coffee-status'), undo=document.querySelector('#coffee-undo');
    let items=[],removed=null;
    try{const saved=JSON.parse(localStorage.getItem('aftertaste:list')||'[]');if(Array.isArray(saved))items=saved.filter(x=>x&&typeof x.id==='string'&&['坚果可可','莓果花香'].includes(x.flavour)&&['整豆','手冲','意式'].includes(x.grind));}catch{ /* Keep an empty local list if storage is unavailable. */ }
    function render(){document.querySelector('#coffee-count').textContent=String(items.length);list.replaceChildren();if(!items.length){const empty=document.createElement('div');empty.className='list-empty';empty.textContent='清单为空';list.append(empty);}for(const item of items){const row=document.createElement('div');row.className='coffee-item';const description=document.createElement('div'),title=document.createElement('strong'),detail=document.createElement('span'),remove=document.createElement('button');title.textContent=item.flavour;detail.textContent=item.grind;description.append(title,detail);remove.textContent='移除';remove.setAttribute('aria-label',`移除 ${item.flavour} ${item.grind}`);remove.addEventListener('click',()=>{removed={item,index:items.indexOf(item)};items=items.filter(x=>x.id!==item.id);save();render();undo.hidden=false;undo.focus();});row.append(description,remove);list.append(row);}}
    function save(){try{localStorage.setItem('aftertaste:list',JSON.stringify(items));status.textContent='已保存到本机清单';}catch{status.textContent='保存失败 清单仅保留在当前页面';}}
    form.addEventListener('submit',event=>{event.preventDefault();const choice=Object.fromEntries(new FormData(form));items.push({id:crypto.randomUUID(),...choice});save();render();});
    undo.addEventListener('click',()=>{if(!removed)return;items.splice(removed.index,0,removed.item);removed=null;save();render();undo.hidden=true;document.querySelector('#list-title').setAttribute('tabindex','-1');document.querySelector('#list-title').focus();});render();
  }
})();
