(() => {
  'use strict';
  const examples = {
    book: '周末书店计划\n\n让附近的人，有一个愿意停留的周末去处。\n\n周六下午两点，举办一场关于城市与阅读的小型分享会。林汐在周三前确认两位分享嘉宾，周言负责海报和店内陈列。\n\n现场保留十二个座位，需要提前预约；同时准备无咖啡因饮品。下周一复盘活动，决定是否每月举办。',
    product: '新产品发布计划\n\n为独立设计师介绍一款新的桌面照明产品。\n\n本周五发布产品介绍页。设计组在周三前完成三张产品图，编辑组负责说明与尺寸信息。\n\n发布前检查手机阅读、键盘操作与图片加载。下周一汇总咨询问题，补充常见问答。',
    meeting: '设计评审纪要\n\n统一新项目的首屏方向，优先让用户理解产品。\n\n林汐周三提交两张构图草图；周言负责整理真实素材。保留原来的导出和撤销功能。\n\n周五一起评审桌面与手机版本，确认下一步。暂不增加账户、积分或新订阅。'
  };
  const source = document.querySelector('#source'), result = document.querySelector('#result');
  const title = document.querySelector('#document-title'), status = document.querySelector('#document-status');
  const run = document.querySelector('#run'), exportButton = document.querySelector('#export');
  let active = 'outline', pending = null, previousSource = null;
  function organize(text) {
    const paragraphs = text.trim().split(/\n\s*\n/).map(t => t.trim()).filter(Boolean);
    const first = (paragraphs.shift() || '未命名文稿').replace(/^#+\s*/, '');
    const heading = first.slice(0, 80);
    const body = paragraphs.length && first.length <= 80 ? paragraphs : [first, ...paragraphs];
    const sentences = body.join('\n').split(/(?<=[。！？；])\s*|\n+/).map(t => t.trim()).filter(Boolean);
    const actions = sentences.filter(t => /负责|确认|完成|准备|提交|检查|汇总|复盘|评审|本周|周[一二三四五六日天]|需要|保留/.test(t));
    return { title: heading, outline: body.map((t, i) => ['想要做到的事', '具体安排', '需要留意', '补充记录'][Math.min(i, 3)] + '\n' + t).join('\n\n'), actions: actions.length ? actions.map((t, i) => `${String(i + 1).padStart(2, '0')}  ${t}`).join('\n\n') : '原文中还没有明确的行动项。你可以补充负责人、任务或时间。' };
  }
  let initial = organize(examples.book);
  let state = { source: examples.book, processed: examples.book, title: initial.title, outline: initial.outline, actions: initial.actions };
  let saveOK = true;
  try {
    const saved = JSON.parse(localStorage.getItem('form:document') || 'null');
    if (saved && ['source', 'processed', 'title', 'outline', 'actions'].every(k => typeof saved[k] === 'string')) state = saved;
  } catch { saveOK = false; }
  function save() {
    try { localStorage.setItem('form:document', JSON.stringify(state)); saveOK = true; }
    catch { saveOK = false; }
    refreshStatus();
  }
  function refreshStatus(message) {
    status.textContent = message || (!saveOK ? '保存失败 请导出备份' : state.source !== state.processed ? '原文已更新' : '已保存');
  }
  function showResult() {
    result.value = state[active];
    document.querySelectorAll('[data-tab]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.tab === active)));
    document.querySelector('#result-label').textContent = (active === 'outline' ? '提纲' : '行动项') + '，可编辑';
  }
  source.value = state.source; title.value = state.title; showResult(); save();
  source.addEventListener('input', () => { state.source = source.value; save(); });
  title.addEventListener('input', () => { state.title = title.value; save(); });
  result.addEventListener('input', () => { state[active] = result.value; save(); });
  document.querySelectorAll('[data-tab]').forEach(button => button.addEventListener('click', () => { active = button.dataset.tab; showResult(); }));
  const undo = document.querySelector('#undo-sample');
  document.querySelectorAll('[data-sample]').forEach(button => button.addEventListener('click', () => {
    previousSource = state.source; state.source = examples[button.dataset.sample]; source.value = state.source; undo.hidden = false; save();
  }));
  undo.addEventListener('click', () => { if (previousSource === null) return; state.source = previousSource; source.value = state.source; previousSource = null; undo.hidden = true; save(); source.focus(); });
  function setBusy(busy) {
    source.readOnly = result.readOnly = title.readOnly = busy;
    exportButton.disabled = busy;
    document.querySelectorAll('[data-sample], #undo-sample').forEach(b => b.disabled = busy);
    document.querySelector('.document-pane').setAttribute('aria-busy', String(busy));
    run.textContent = busy ? '取消整理' : '整理文稿 ↗';
  }
  run.addEventListener('click', () => {
    if (pending !== null) {
      clearTimeout(pending); pending = null; setBusy(false); refreshStatus('已取消 保留原结果'); return;
    }
    if (!source.value.trim()) { refreshStatus('请先输入原文'); source.focus(); return; }
    const snapshot = source.value;
    setBusy(true); refreshStatus('整理中');
    pending = setTimeout(() => {
      const organized = organize(snapshot);
      state = { ...state, ...organized, processed: snapshot };
      title.value = state.title; pending = null; showResult(); setBusy(false); save();
    }, 650);
  });
  exportButton.addEventListener('click', () => {
    const blob = new Blob([state.title + '\n\n' + state[active]], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = `FORM-${active === 'outline' ? '提纲' : '行动项'}.txt`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); refreshStatus('已导出');
  });
})();
