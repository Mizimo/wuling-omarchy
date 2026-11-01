// Dispatch 調度 — interactive prototype: WULING's own launcher with modes, opened with Super+D; Super+Space stays Omarchy's menu.
//   dispatch.html?dir=field|hud&theme=mist|paper&mode=apps|clip|run|calc|ask&q=…&sel=0
// Nothing is executed: an action shows the command it would run.
const PV = new URLSearchParams(location.search);
document.documentElement.classList.add('proto');

const ICON = (n) => (window.ICONS && window.ICONS[n]) || n;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const DEMO_APPS = [
  ['Foot', '終端機', 'SYS', 'terminal'], ['Chromium', '網頁瀏覽器', 'WEB', 'public'], ['Neovim', '文字編輯器', 'DEV', 'code'],
  ['Files', '檔案管理', 'SYS', 'folder'], ['Obsidian', '筆記', 'OFFICE', 'edit_note'], ['Signal', '通訊', 'NET', 'chat'],
  ['Spotify', '音樂', 'MEDIA', 'music_note'], ['LocalSend', '傳送檔案', 'NET', 'send'], ['btop', '系統監看', 'SYS', 'monitoring'],
  ['Calculator', '計算機', 'UTIL', 'calculate'], ['Docker', '容器', 'DEV', 'deployed_code'], ['Typora', 'Markdown 編輯', 'OFFICE', 'description'],
];
const DEMO_CLIPS = [['git commit -m "bar: anchor the clock"', '14:01'], ['https://omarchy.org/docs', '13:52'], ['11.01 review at 15:00', '13:40'],
  ['#FEF700', '13:12'], ['omarchy plugin list --json', '12:58']];
// ------------------------------------------------------------------ state
const st = { q: '', sel: 0, mode: 'apps' };
// Ask 詢問 hands the text to the default agent through Omarchy's own `omarchy agent prompt`
const MODES = [['apps', 'Apps 應用'], ['clip', 'Clip 剪貼'], ['run', 'Run 執行'], ['calc', 'Calc 計算'], ['ask', 'Ask 詢問']];

function match(label, q) { // case-insensitive subsequence; returns highlighted html or null
  if (!q) return esc(label);
  const L = label.toLowerCase(), Q = q.toLowerCase();
  const at = L.indexOf(Q);
  if (at >= 0) return esc(label.slice(0, at)) + '<em>' + esc(label.slice(at, at + q.length)) + '</em>' + esc(label.slice(at + q.length));
  let i = 0, out = '';
  for (const ch of label) { if (i < Q.length && ch.toLowerCase() === Q[i]) { out += '<em>' + esc(ch) + '</em>'; i++; } else out += esc(ch); }
  return i === Q.length ? out : null;
}
function score(label, aliases, q) {
  const L = label.toLowerCase(), Q = q.toLowerCase();
  if (L === Q) return 100; if (L.startsWith(Q)) return 80;
  if (L.split(/[\s\-·]+/).some((w) => w.startsWith(Q))) return 60;
  if ((aliases || []).some((a) => a.toLowerCase().startsWith(Q))) return 50;
  if (L.includes(Q)) return 40; return match(label, q) ? 10 : 0;
}

function rows() {
  const q = st.q.replace(/^[=>?]/, '');
  if (st.mode === 'apps') return DEMO_APPS.map((a, i) => ({ a, s: q ? score(a[0], [a[1]], q) : 50 - i, hl: match(a[0], q) }))
    .filter((r) => r.hl !== null && r.s > 0).sort((x, y) => y.s - x.s);
  if (st.mode === 'clip') return DEMO_CLIPS.map((c) => ({ c, hl: match(c[0], q) })).filter((r) => r.hl !== null);
  if (st.mode === 'run') return [{ run: q || 'omarchy update', hl: esc(q || 'omarchy update') }, { run: 'btop', hl: 'btop', recent: 1 }, { run: 'omarchy plugin list', hl: 'omarchy plugin list', recent: 1 }];
  if (st.mode === 'ask') return [{ ask: q || '把頂欄移到下面', hl: esc(q || '把頂欄移到下面') }, { ask: '為什麼 Wi-Fi 一直斷線？', hl: '為什麼 Wi-Fi 一直斷線？', recent: 1 }];
  return [];
}
function calc(q) {
  const e = q.replace(/^=/, '').replace(/×/g, '*').replace(/÷/g, '/').replace(/\^/g, '**');
  if (!e.trim() || /[^0-9+\-*/().%\s*]/.test(e)) return null;
  try { const v = Function(`"use strict";return (${e})`)(); return Number.isFinite(v) ? v : null; } catch { return null; }
}

// ------------------------------------------------------------------ render
function render() {
  const d = document.querySelector('.dsp');
  const list = d.querySelector('.list'), meta = d.querySelector('.meta'), tabs = d.querySelector('.tabs');
  let out = [];
    if (st.q.startsWith('=')) st.mode = 'calc'; else if (st.q.startsWith('>')) st.mode = 'run'; else if (st.q.startsWith('?')) st.mode = 'ask';
    tabs.innerHTML = MODES.map(([k, l]) => `<span class="${k === st.mode ? 'on' : ''}" data-mode="${k}">${l}</span>`).join('');
    d.querySelector('.rail .mode').textContent = `Dispatch · ${st.mode}`;
    if (st.mode === 'calc') {
      const v = calc(st.q || '=1366*768');
      meta.innerHTML = `<span class="micro">Result 結果 · Engine JS</span><span class="micro rt">⏎ copies</span>`;
      list.innerHTML = `<div class="calc"><div class="res">${v === null ? '—' : esc(v.toLocaleString('en-US').replace(/,/g, ' '))}</div>
        <div class="ex">${esc((st.q || '=1366*768').replace(/^=/, ''))} =</div></div>`;
      out = v === null ? [] : [{ v }];
    } else {
      out = rows();
      meta.innerHTML = `<span class="micro">Match ${out.length} · Sort ${st.mode === 'apps' ? 'Frecency' : 'Recent'}</span><span class="micro rt">${st.q ? `Query "${esc(st.q)}"` : ''}</span>`;
      list.innerHTML = out.map((r, i) => {
        const [ic, nm, dt, chip, go] = st.mode === 'apps' ? [r.a[3], r.hl, r.a[1], r.a[2], '⏎ Launch']
          : st.mode === 'clip' ? ['content_paste', r.hl, '', r.c[1], '⏎ Paste']
          : st.mode === 'ask' ? [r.recent ? 'history' : 'smart_toy', r.hl, r.recent ? 'recent' : 'Claude Code · 預設的 agent', 'Agent', '⏎ Ask']
          : [r.recent ? 'history' : 'terminal', r.hl, r.recent ? 'recent' : 'in Foot', 'Run', '⏎ Run'];
        return `<div class="row ${i === st.sel ? 'sel' : ''}" data-i="${i}"><span class="ix">${String(i + 1).padStart(3, '0')}</span>
          <span class="msym">${ICON(ic)}</span><span class="nm">${nm}</span><span class="dt">${esc(dt)}</span><span class="chip">${esc(chip)}</span><span class="go">${go}</span></div>`;
      }).join('') || `<div class="empty">沒有符合的項目。</div>`;
    }
  st.rows = out;
  const s = list.querySelector('.row.sel'); if (s) s.scrollIntoView({ block: 'nearest' });
}

function say(html) {
  const t = document.querySelector('.toastline'); t.innerHTML = html; t.classList.add('on');
  clearTimeout(say.t); say.t = setTimeout(() => t.classList.remove('on'), 2600);
}
function activate(i = st.sel) {
  const r = st.rows && st.rows[i]; if (!r) return;
  const row = document.querySelector(`.row[data-i="${i}"]`); if (row) { row.classList.remove('flash'); void row.offsetWidth; row.classList.add('flash'); }
  if (st.mode === 'calc') return say(`<b>Copied</b> ${esc(String(r.v))}`);
  if (st.mode === 'apps') return say(`<b>Launch</b> ${esc(r.a[0])}`);
  if (st.mode === 'clip') return say(`<b>Paste</b> <span style="text-transform:none">${esc(r.c[0])}</span>`);
  if (st.mode === 'ask') return say(`<b>Ask</b> <span style="text-transform:none">omarchy agent prompt "${esc(r.ask)}"</span>`);
  return say(`<b>Run</b> <span style="text-transform:none">${esc(r.run)}</span> · Foot`);
}
function back() {
  if (st.q) { st.q = ''; input().value = ''; } else return say('<b>Esc</b> 關閉 Dispatch');
  st.sel = 0; render();
}
const input = () => document.querySelector('.dsp .q input');

// ------------------------------------------------------------------ build the frame + chrome
document.addEventListener('DOMContentLoaded', () => {
  const stage = document.querySelector('.stage');
  stage.insertAdjacentHTML('beforeend', `<div class="dsp">
    <div class="rail"><span class="no">01</span><span class="zh">調度</span><span class="mode">Dispatch · Apps</span><span class="seal">令</span></div>
    <div class="main"><div class="q"><input placeholder="搜尋 · = 計算 · > 執行 · ? 問 agent" autocomplete="off" spellcheck="false"><div class="tabs"></div></div>
      <div class="meta"></div><div class="list"></div>
      <div class="foot micro"><span>↑↓ Select</span><span><b>⏎</b> Launch</span><span><b>Tab</b> Mode</span><span><b>Esc</b> Close</span>
        <span class="rt">Super+D · Super+Space stays Omarchy</span></div></div></div>
    <div class="toastline"></div>`);
  const link = (o) => { const p = new URLSearchParams(location.search); for (const k in o) p.set(k, o[k]); return '?' + p.toString(); };
  const b = (k, v, l) => `<button class="${(PV.get(k) || { dir: 'field', theme: 'mist' }[k]) === v ? 'on' : ''}" onclick="location.search='${link({ [k]: v })}'">${l}</button>`;
  document.body.insertAdjacentHTML('afterbegin', `<div class="chrome">
    <div class="grp"><span>預設</span>${b('dir', 'field', '照舊')}${b('dir', 'hud', '更強烈')}</div>
    <div class="grp"><span>主題</span>${b('theme', 'mist', 'MIST')}${b('theme', 'paper', 'PAPER')}</div>
    <span class="hint">打字搜尋 · ↑↓ 選 · Enter 開 · Esc 關閉 · Tab 換模式 · 不會真的執行任何東西</span></div>`);
  const fit = () => { if (innerWidth > 760) stage.style.transform = `scale(${Math.min(innerWidth / 1366, (innerHeight - 44) / 768)})`; };
  addEventListener('resize', fit); fit();
  const inp = input();
  inp.addEventListener('input', () => { st.q = inp.value; st.sel = 0; render(); });
  inp.addEventListener('keydown', (e) => {
    const n = (st.rows || []).length;
    if (e.key === 'ArrowDown') { st.sel = Math.min(n - 1, st.sel + 1); render(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { st.sel = Math.max(0, st.sel - 1); render(); e.preventDefault(); }
    else if (e.key === 'Enter') { activate(); e.preventDefault(); }
    else if (e.key === 'Escape') { back(); e.preventDefault(); }
    else if (e.key === 'Tab') { const i = MODES.findIndex(([k]) => k === st.mode); st.mode = MODES[(i + (e.shiftKey ? MODES.length - 1 : 1)) % MODES.length][0];
      if (/^[=>?]/.test(st.q)) { st.q = ''; inp.value = ''; } st.sel = 0; render(); e.preventDefault(); }
  });
  document.querySelector('.dsp').addEventListener('click', (e) => {
    const row = e.target.closest('.row[data-i]'), mode = e.target.closest('[data-mode]');
    if (row) { const i = +row.dataset.i; if (i === st.sel) activate(i); else { st.sel = i; render(); } }
    else if (mode) { st.mode = mode.dataset.mode; st.sel = 0; render(); }
    if (innerWidth > 760) inp.focus();
  });
  // a starting state from the URL: &q=… &mode=calc &sel=2
  if (PV.get('mode')) st.mode = PV.get('mode');
  if (PV.get('q')) { st.q = PV.get('q'); inp.value = st.q; }
  if (PV.get('sel')) st.sel = +PV.get('sel');
  render();
  if (innerWidth > 760) inp.focus();
});
