// Dispatch 調度 — interactive prototype for the design report.
//   proto.html?v=a|b&dir=as|calm|bold&theme=mist|paper
// 甲 (v=a) walks Omarchy's own menu tree (window.MENU, parsed from 4.0.6) exactly as Omarchy does: same entries,
// same levels, Enter opens, Esc goes back, typing searches the whole tree. Only the drawing is WULING's.
// 乙 (v=b) is WULING's own launcher with modes, on its own key; Super+Space stays Omarchy's menu.
// Nothing is executed: an action shows the command it would run.
const PV = new URLSearchParams(location.search);
const V = PV.get('v') === 'b' ? 'b' : 'a';
document.documentElement.classList.add('proto');

const ICON = (n) => (window.ICONS && window.ICONS[n]) || n;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const DEMO_APPS = [
  ['Alacritty', '終端機', 'SYS', 'terminal'], ['Chromium', '網頁瀏覽器', 'WEB', 'public'], ['Neovim', '文字編輯器', 'DEV', 'code'],
  ['Files', '檔案管理', 'SYS', 'folder'], ['Obsidian', '筆記', 'OFFICE', 'edit_note'], ['Signal', '通訊', 'NET', 'chat'],
  ['Spotify', '音樂', 'MEDIA', 'music_note'], ['LocalSend', '傳送檔案', 'NET', 'send'], ['btop', '系統監看', 'SYS', 'monitoring'],
  ['Calculator', '計算機', 'UTIL', 'calculate'], ['Docker', '容器', 'DEV', 'deployed_code'], ['Typora', 'Markdown 編輯', 'OFFICE', 'description'],
];
const DEMO_CLIPS = [['git commit -m "bar: anchor the clock"', '14:01'], ['https://omarchy.org/docs', '13:52'], ['11.01 review at 15:00', '13:40'],
  ['#FEF700', '13:12'], ['omarchy plugin list --json', '12:58']];
const ROOT_ICONS = { apps: 'apps', learn: 'school', trigger: 'bolt', style: 'palette', setup: 'tune', install: 'download', remove: 'delete',
  update: 'update', about: 'info', system: 'power_settings_new', 'system.screensaver': 'monitor', 'system.lock': 'lock',
  'system.suspend': 'bedtime', 'system.hibernate': 'downloading', 'system.logout': 'logout', 'system.reboot': 'restart_alt',
  'system.shutdown': 'power_settings_new' };
const HOLD = new Set(['system.logout', 'system.reboot', 'system.shutdown']);

// ------------------------------------------------------------------ Omarchy's tree (甲)
const items = new Map(), kids = new Map();
for (const [order, it] of ((window.MENU && window.MENU.items) || []).entries()) {
  it.order = order;
  items.set(it.id, it);
  if (!kids.has(it.parent)) kids.set(it.parent, []);
  kids.get(it.parent).push(it.id);
}
// providers fill these submenus at runtime in Omarchy; the prototype uses neutral demo rows
kids.set('apps', DEMO_APPS.map((a, i) => { const id = `app:${i}`; items.set(id, { id, parent: 'apps', kind: 'app', label: a[0], detail: a[1], cat: a[2], icon: a[3], order: 1000 + i }); return id; }));
const pathOf = (id) => { const out = []; let c = items.get(id); while (c && c.id !== 'root') { out.unshift(c.label); c = items.get(c.parent); } return out; };
const iconOf = (it) => it.kind === 'app' ? it.icon : ROOT_ICONS[it.id] || (it.kind === 'menu' ? 'folder' : it.kind === 'link' ? 'open_in_new' : 'bolt');

// ------------------------------------------------------------------ state
const st = { stack: ['root'], q: '', sel: 0, mode: 'apps' };
// Ask 詢問 hands the text to the default agent through Omarchy's own `omarchy agent prompt` (the agents option, level 3)
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

// Omarchy's own search rules (shell/plugins/menu/MenuModel.js 4.0.6: nameSearchText, matchesQuery, searchScore):
// every term must appear in the label, the leaf id or an alias, or be a whole word of the description;
// lower score wins — exact, prefix, substring, name, description; menus and links −2, apps −5; then depth and order.
const tok = (v) => String(v || '').replace(/[._-]+/g, ' ');
const nameText = (it) => [it.label, tok(String(it.id).split('.').pop()), (it.aliases || []).map(tok).join(' ')].join(' ').toLowerCase();
const inWords = (t, text) => String(text || '').toLowerCase().split(/\s+/).includes(t);
const depthOf = (it) => { let d = 0, c = it; while (c && c.parent && c.parent !== 'root' && d < 32) { d++; c = items.get(c.parent); } return d; };
function oMatches(it, q) { const nt = nameText(it), dt = String(it.description || '').toLowerCase();
  return q.toLowerCase().trim().split(/\s+/).every((t) => !t || nt.includes(t) || inWords(t, dt)); }
function oScore(it, q) {
  const n = q.toLowerCase().trim(), label = it.label.toLowerCase(), nt = nameText(it), dt = String(it.description || '').toLowerCase();
  let s = 80;
  if (label === n) s = it.parent === 'root' ? 2 : 0;
  else if (it.kind === 'app' && label.split(/\s+/).includes(n)) s = 0;
  else if (label.startsWith(n)) s = 10; else if (label.includes(n)) s = 30; else if (nt.includes(n)) s = 40;
  else if (n.split(/\s+/).every((t) => inWords(t, dt))) s = 60;
  if (it.kind === 'menu' || it.kind === 'link') s -= 2;
  if (it.kind === 'app') s -= 5;
  return s * 1000 + depthOf(it) * 25 + (it.order || 0);
}
function hlTerms(label, q) { // mark every term's first occurrence in the label
  let out = esc(label);
  for (const t of q.toLowerCase().trim().split(/\s+/).filter(Boolean)) {
    const i = out.toLowerCase().indexOf(esc(t)); if (i >= 0 && !out.slice(0, i).endsWith('<em>')) out = out.slice(0, i) + '<em>' + out.slice(i, i + esc(t).length) + '</em>' + out.slice(i + esc(t).length);
  }
  return out;
}
function rowsA() {
  if (st.q) {
    const out = [];
    for (const it of items.values()) if (it.id !== 'root' && oMatches(it, st.q)) out.push({ it, s: oScore(it, st.q), hl: hlTerms(it.label, st.q), dt: pathOf(it.parent).join(' › ') || 'Omarchy' });
    out.sort((a, b) => a.s - b.s);
    return out.slice(0, 80);
  }
  const cur = st.stack[st.stack.length - 1];
  return (kids.get(cur) || []).map((id) => {
    const it = items.get(id), n = (kids.get(id) || []).length;
    return { it, hl: esc(it.label), dt: it.kind === 'menu' ? `${n} 項` : it.kind === 'app' ? it.detail : (it.description || '') };
  });
}
function rowsB() {
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
  let rows = [];
  if (V === 'a') {
    rows = rowsA();
    const crumbs = ['Root', ...st.stack.slice(1).map((id) => items.get(id).label)];
    meta.innerHTML = `<button class="back micro" style="background:none;border:1px solid var(--line);color:var(--paper-2);padding:3px 6px">‹ Back</button>
      <div class="crumb micro">${st.q ? `<span>Search 搜尋 · whole menu</span>` : crumbs.map((c, i) => `<b data-depth="${i}">${esc(c)}</b>`).join('<span>›</span>')}</div>
      <span class="micro rt">${rows.length} ${st.q ? 'matches' : 'entries'}</span>`;
    list.innerHTML = rows.length ? rows.map((r, i) => {
      const it = r.it, chip = it.kind === 'menu' ? 'Menu' : it.kind === 'app' ? it.cat : HOLD.has(it.id) ? 'Hold 長按' : it.kind === 'link' ? 'Link' : 'Run';
      const go = it.kind === 'menu' ? '⏎ Open' : it.kind === 'app' ? '⏎ Launch' : HOLD.has(it.id) ? 'Hold ⏎' : '⏎ Run';
      return `<div class="row ${i === st.sel ? 'sel' : ''}" data-i="${i}"><span class="ix">${String(i + 1).padStart(3, '0')}</span>
        <span class="msym">${ICON(iconOf(it))}</span><span class="nm">${r.hl}</span><span class="dt">${esc(r.dt || '')}</span>
        <span class="chip">${esc(chip)}</span><span class="go">${go}</span></div>`;
    }).join('') : `<div class="empty">沒有符合「${esc(st.q)}」的項目。Omarchy 的選單裡找不到它。</div>`;
  } else {
    if (st.q.startsWith('=')) st.mode = 'calc'; else if (st.q.startsWith('>')) st.mode = 'run'; else if (st.q.startsWith('?')) st.mode = 'ask';
    tabs.innerHTML = MODES.map(([k, l]) => `<span class="${k === st.mode ? 'on' : ''}" data-mode="${k}">${l}</span>`).join('');
    d.querySelector('.rail .mode').textContent = `Dispatch · ${st.mode}`;
    if (st.mode === 'calc') {
      const v = calc(st.q || '=1366*768');
      meta.innerHTML = `<span class="micro">Result 結果 · Engine JS</span><span class="micro rt">⏎ copies</span>`;
      list.innerHTML = `<div class="calc"><div class="res">${v === null ? '—' : esc(v.toLocaleString('en-US').replace(/,/g, ' '))}</div>
        <div class="ex">${esc((st.q || '=1366*768').replace(/^=/, ''))} =</div></div>`;
      rows = v === null ? [] : [{ v }];
    } else {
      rows = rowsB();
      meta.innerHTML = `<span class="micro">Match ${rows.length} · Sort ${st.mode === 'apps' ? 'Frecency' : 'Recent'}</span><span class="micro rt">${st.q ? `Query "${esc(st.q)}"` : ''}</span>`;
      list.innerHTML = rows.map((r, i) => {
        const [ic, nm, dt, chip, go] = st.mode === 'apps' ? [r.a[3], r.hl, r.a[1], r.a[2], '⏎ Launch']
          : st.mode === 'clip' ? ['content_paste', r.hl, '', r.c[1], '⏎ Paste']
          : st.mode === 'ask' ? [r.recent ? 'history' : 'smart_toy', r.hl, r.recent ? 'recent' : 'Claude Code · 預設的 agent', 'Agent', '⏎ Ask']
          : [r.recent ? 'history' : 'terminal', r.hl, r.recent ? 'recent' : 'in Alacritty', 'Run', '⏎ Run'];
        return `<div class="row ${i === st.sel ? 'sel' : ''}" data-i="${i}"><span class="ix">${String(i + 1).padStart(3, '0')}</span>
          <span class="msym">${ICON(ic)}</span><span class="nm">${nm}</span><span class="dt">${esc(dt)}</span><span class="chip">${esc(chip)}</span><span class="go">${go}</span></div>`;
      }).join('') || `<div class="empty">沒有符合的項目。</div>`;
    }
  }
  st.rows = rows;
  const s = list.querySelector('.row.sel'); if (s) s.scrollIntoView({ block: 'nearest' });
}

function say(html) {
  const t = document.querySelector('.toastline'); t.innerHTML = html; t.classList.add('on');
  clearTimeout(say.t); say.t = setTimeout(() => t.classList.remove('on'), 2600);
}
function activate(i = st.sel) {
  const r = st.rows && st.rows[i]; if (!r) return;
  const row = document.querySelector(`.row[data-i="${i}"]`); if (row) { row.classList.remove('flash'); void row.offsetWidth; row.classList.add('flash'); }
  if (V === 'a') {
    const it = r.it;
    if (it.kind === 'menu') { st.stack = st.q ? ['root', ...ancestors(it.id), it.id] : [...st.stack, it.id]; st.q = ''; st.sel = 0; input().value = ''; render(); return; }
    if (it.kind === 'app') return say(`<b>Launch</b> ${esc(it.label)} · 經由 Omarchy 啟動，不屬於 shell`);
    if (HOLD.has(it.id)) return say(`<b>Hold</b> ${esc(it.label)} · 長按 0.8 秒才會執行（電源選單的規則）`);
    return say(`<b>${it.kind === 'link' ? 'Open' : 'Run'}</b> <span style="text-transform:none">${esc(it.action || it.target || it.label)}</span>`);
  }
  if (st.mode === 'calc') return say(`<b>Copied</b> ${esc(String(r.v))}`);
  if (st.mode === 'apps') return say(`<b>Launch</b> ${esc(r.a[0])}`);
  if (st.mode === 'clip') return say(`<b>Paste</b> <span style="text-transform:none">${esc(r.c[0])}</span>`);
  if (st.mode === 'ask') return say(`<b>Ask</b> <span style="text-transform:none">omarchy agent prompt "${esc(r.ask)}"</span>`);
  return say(`<b>Run</b> <span style="text-transform:none">${esc(r.run)}</span> · Alacritty`);
}
function ancestors(id) { const out = []; let c = items.get(items.get(id).parent); while (c && c.id !== 'root') { out.unshift(c.id); c = items.get(c.parent); } return out; }
function back() {
  if (st.q) { st.q = ''; input().value = ''; }
  else if (V === 'a' && st.stack.length > 1) st.stack.pop();
  else return say(V === 'a' ? '<b>Esc</b> 關閉選單（和 Omarchy 一樣）' : '<b>Esc</b> 關閉 Dispatch');
  st.sel = 0; render();
}
const input = () => document.querySelector('.dsp .q input');

// ------------------------------------------------------------------ build the frame + chrome
document.addEventListener('DOMContentLoaded', () => {
  const stage = document.querySelector('.stage');
  stage.insertAdjacentHTML('beforeend', `<div class="dsp">
    <div class="rail"><span class="no">01</span><span class="zh">調度</span><span class="mode">${V === 'a' ? 'Dispatch · Menu' : 'Dispatch · Apps'}</span><span class="seal">令</span></div>
    <div class="main"><div class="q"><input placeholder="${V === 'a' ? '搜尋 Omarchy 的選單 · Search' : '搜尋 · = 計算 · > 執行 · ? 問 agent'}" autocomplete="off" spellcheck="false">
      ${V === 'b' ? '<div class="tabs"></div>' : ''}</div>
      <div class="meta"></div><div class="list"></div>
      <div class="foot micro"><span>↑↓ Select</span><span><b>⏎</b> ${V === 'a' ? 'Open' : 'Launch'}</span>${V === 'b' ? '<span><b>Tab</b> Mode</span>' : ''}<span><b>Esc</b> ${V === 'a' ? 'Back' : 'Close'}</span>
        <span class="rt">${V === 'a' ? 'Omarchy menu 4.0.6 · Super+Space' : 'Super+D · Super+Space stays Omarchy'}</span></div></div></div>
    <div class="toastline"></div>`);
  const link = (o) => { const p = new URLSearchParams(location.search); for (const k in o) p.set(k, o[k]); return '?' + p.toString(); };
  const b = (k, v, l) => `<button class="${(PV.get(k) || { v: 'a', dir: 'as', theme: 'mist' }[k]) === v ? 'on' : ''}" onclick="location.search='${link({ [k]: v })}'">${l}</button>`;
  document.body.insertAdjacentHTML('afterbegin', `<div class="chrome">
    <div class="grp"><span>Dispatch</span>${b('v', 'a', '甲 照 Omarchy')}${b('v', 'b', '乙 另一個鍵')}</div>
    <div class="grp"><span>方向</span>${b('dir', 'as', '照舊')}${b('dir', 'calm', '克制')}${b('dir', 'bold', '強烈')}</div>
    <div class="grp"><span>主題</span>${b('theme', 'mist', 'MIST')}${b('theme', 'paper', 'PAPER')}</div>
    <span class="hint">打字搜尋 · ↑↓ 選 · Enter 開 · Esc 返回${V === 'b' ? ' · Tab 換模式' : ''} · 不會真的執行任何東西</span></div>`);
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
    else if (e.key === 'Backspace' && !inp.value && V === 'a' && st.stack.length > 1) { back(); e.preventDefault(); }
    else if (e.key === 'Tab' && V === 'b') { const i = MODES.findIndex(([k]) => k === st.mode); st.mode = MODES[(i + (e.shiftKey ? MODES.length - 1 : 1)) % MODES.length][0];
      if (/^[=>?]/.test(st.q)) { st.q = ''; inp.value = ''; } st.sel = 0; render(); e.preventDefault(); }
  });
  document.querySelector('.dsp').addEventListener('click', (e) => {
    const row = e.target.closest('.row[data-i]'), crumb = e.target.closest('[data-depth]'), mode = e.target.closest('[data-mode]');
    if (row) { const i = +row.dataset.i; if (i === st.sel) activate(i); else { st.sel = i; render(); } }
    else if (crumb) { st.stack = st.stack.slice(0, +crumb.dataset.depth + 1); st.sel = 0; render(); }
    else if (mode) { st.mode = mode.dataset.mode; st.sel = 0; render(); }
    else if (e.target.closest('.back')) back();
    if (innerWidth > 760) inp.focus();
  });
  // a starting state from the URL (used to render the report's frames): &q=… &path=setup.security &mode=calc &sel=2
  if (PV.get('path') && items.has(PV.get('path'))) st.stack = ['root', ...ancestors(PV.get('path')), PV.get('path')];
  if (PV.get('mode')) st.mode = PV.get('mode');
  if (PV.get('q')) { st.q = PV.get('q'); inp.value = st.q; }
  if (PV.get('sel')) st.sel = +PV.get('sel');
  render();
  if (innerWidth > 760) inp.focus();
});
