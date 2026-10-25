(() => {
  'use strict';
  const dialog = document.querySelector('#booking-dialog');
  const form = document.querySelector('#booking-form');
  const summary = document.querySelector('#booking-summary');
  const status = document.querySelector('#booking-status');
  let opener;
  function showPlan(slot) { summary.textContent = `已保存 ${slot}`; summary.hidden = false; }
  try { const plan = localStorage.getItem('aura:local-listening-plan'); if (['周六 14:00', '周日 15:00'].includes(plan)) showPlan(plan); } catch { /* Initial plan is optional. */ }
  document.querySelectorAll('[data-book]').forEach(button => button.addEventListener('click', () => {
    opener = button; status.textContent = '仅本机保存 不提交预约或付款'; dialog.showModal();
  }));
  document.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => opener?.focus());
  form.addEventListener('submit', event => {
    event.preventDefault();
    const slot = new FormData(form).get('slot');
    if (!['周六 14:00', '周日 15:00'].includes(slot)) return;
    try { localStorage.setItem('aura:local-listening-plan', slot); showPlan(slot); status.textContent = `已保存 ${slot}`; }
    catch { status.textContent = '保存失败 请重试'; }
  });
})();
